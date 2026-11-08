"""Validate the specification-only Python API against shared wire contracts."""

import ast
import json


def check_api(root):
    folder = root / 'contracts/quant/v1'
    api = json.loads((folder/'python-api.json').read_text())
    defs = json.loads((folder/'schema.json').read_text())['$defs']
    registry = json.loads((folder/'methods.json').read_text())
    policy = json.loads((folder/'policy.json').read_text())
    tree = ast.parse((root/api['declaration']).read_text())
    classes = {n.name:n for n in tree.body if isinstance(n,ast.ClassDef)}
    aliases = {n.target.id:ast.unparse(n.value) for n in tree.body
               if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name)}

    def shape(schema):
        if '$ref' in schema:
            name = schema['$ref'].split('/')[-1]
            if name in ('Decimal','NonNegativeDecimal'):
                return 'Decimal'
            if name == 'Timestamp':
                return 'datetime'
            if name in api['models']:
                return name
            return shape(defs[name])
        if 'enum' in schema:
            return 'Literal['+', '.join(repr(v) for v in schema['enum'])+']'
        if 'const' in schema:
            return 'Literal['+repr(schema['const'])+']'
        return {'string':'str','integer':'int','boolean':'bool'}[schema['type']]

    def annotation(text):
        return aliases.get(text,text)

    def result_schema(name):
        result = defs[registry['responses'][name]]['properties']['result']
        return defs[result['$ref'].split('/')[-1]] if '$ref' in result else result

    for name,definition in api['models'].items():
        rule = result_schema('context.submit_order') if definition.endswith('.result') else defs[definition]
        fields = {n.target.id:n for n in classes[name].body if isinstance(n,ast.AnnAssign)}
        if fields.keys() != rule['properties'].keys():
            raise ValueError('Python model fields differ from schema: '+name)
        for field,node in fields.items():
            declared = ast.unparse(node.annotation)
            optional = field not in rule.get('required',[])
            if optional:
                if not declared.endswith(' | None') or not isinstance(node.value,ast.Constant) or node.value.value is not None:
                    raise ValueError('optional model field must default to None: '+field)
                declared = declared.removesuffix(' | None')
            if annotation(declared) != shape(rule['properties'][field]):
                raise ValueError('Python field type differs from schema: '+name+'.'+field)

    signatures = {c.name+'.'+m.name:ast.unparse(m.args)+' -> '+ast.unparse(m.returns)
                  for c in tree.body if isinstance(c,ast.ClassDef) and c.name in ('Context','Strategy')
                  for m in c.body if isinstance(m,ast.FunctionDef)}
    if signatures != api['signatures']:
        raise ValueError('Python signatures/defaults differ from frozen API map')

    context = {n.name:n for n in classes['Context'].body if isinstance(n,ast.FunctionDef)}
    properties = {name for name,node in context.items() if any(isinstance(d,ast.Name) and d.id=='property' for d in node.decorator_list)}
    if properties != set(api['context_properties']) or context.keys()-properties != api['methods'].keys():
        raise ValueError('Python Context surface differs from API map')
    if {m['ipc'] for m in api['methods'].values()} != {m for m in registry['requests'] if m.startswith('context.')}:
        raise ValueError('Python Context does not cover wire methods exactly')
    for name,spec in api['methods'].items():
        request = defs[registry['requests'][spec['ipc']]]
        payload = request['properties']['params']['properties']['payload']
        if '$ref' in payload:
            payload = defs[payload['$ref'].split('/')[-1]]
        if set(spec['payload']) != set(payload['properties']):
            raise ValueError('Python payload mapping mismatch: '+name)
        args = context[name].args
        arg_types = {a.arg:ast.unparse(a.annotation) for a in args.args+args.kwonlyargs if a.arg!='self'}
        if set(arg_types)-set(spec['payload']):
            raise ValueError('unmapped Python method argument: '+name)
        for field,declared in arg_types.items():
            base = declared.removesuffix(' | None')
            if annotation(base) != shape(payload['properties'][field]):
                raise ValueError('Python parameter type differs from wire: '+name+'.'+field)
        declared_return = ast.unparse(context[name].returns)
        result = defs[registry['responses'][spec['ipc']]]['properties']['result']
        if declared_return.startswith('tuple['):
            if result != {'type':'array','items':{'$ref':'#/$defs/Bar'}}:
                raise ValueError('history return mapping mismatch')
        elif declared_return not in api['models'] or result_schema(spec['ipc']) != (
            result_schema('context.submit_order') if declared_return=='OrderSubmission'
            else defs[api['models'][declared_return]]
        ):
            raise ValueError('Python result type differs from wire: '+name)
        if spec['permission'] not in policy['phases']['bar']:
            raise ValueError('unknown Python phase permission')
    strategy = {n.name:n for n in classes['Strategy'].body if isinstance(n,ast.FunctionDef)}
    expected = {'on_start':'self, context: Context','on_bar':'self, bar: Bar','on_stop':'self'}
    if set(api['lifecycle']) != set(expected):
        raise ValueError('Python lifecycle map incomplete')
    for name,signature in expected.items():
        if ast.unparse(strategy[name].args)!=signature or ast.unparse(strategy[name].returns)!='None':
            raise ValueError('Python lifecycle signature changed: '+name)
        if api['lifecycle'][name] not in registry['requests']:
            raise ValueError('Python lifecycle wire mapping missing')
    codes = defs['Error']['properties']['error']['properties']['data']['properties']['code']['enum']
    if set(codes)!=set(api['errors']):
        raise ValueError('Python error map incomplete')
    for name in api['errors'].values():
        if [ast.unparse(b) for b in classes[name].bases]!=['HostedError']:
            raise ValueError('Python exception hierarchy mismatch')
    return {'module':api['public_module'],'status':api['status'],'context_methods':len(api['methods']),
            'models':len(api['models']),'business_errors':len(codes)}
