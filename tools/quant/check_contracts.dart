import 'dart:convert';
import 'dart:io';

// This stdlib-only CLI must also run without pub resolution or Flutter setup.
// ignore: avoid_relative_lib_imports
import '../../lib/app/quant/contracts/schema_validator.dart';
// ignore: avoid_relative_lib_imports
import '../../lib/app/quant/contracts/strict_json.dart';

void main(List<String> arguments) {
  final root = arguments.isEmpty ? Directory.current.path : arguments.single;
  final directory = '$root/contracts/quant/v1';
  final schema = QuantSchemaValidator(
      jsonDecode(File('$directory/schema.json').readAsStringSync())
          as Map<String, dynamic>);
  final messages =
      jsonDecode(File('$directory/messages.json').readAsStringSync())
          as Map<String, dynamic>;
  var failures = 0;
  for (final item in messages['cases'] as List) {
    var accepted = true;
    try {
      final value = item.containsKey('raw')
          ? decodeQuantJson(item['raw'] as String)
          : item['value'];
      schema.validate(item['definition'] as String, value);
    } on QuantContractViolation {
      accepted = false;
    } on FormatException {
      accepted = false;
    }
    if (accepted != item['valid']) {
      stderr.writeln('FAIL ${item['name']}: accepted=$accepted');
      failures++;
    }
  }
  if (failures != 0) exit(1);
  stdout.writeln(
      'Dart P0 shared messages: ${(messages['cases'] as List).length} passed');
}
