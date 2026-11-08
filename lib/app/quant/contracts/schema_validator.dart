/// Language-neutral P0 schema adapter. No UI, platform, network, or package
/// dependencies. This validates contracts, not strategy execution or matching.
class QuantContractViolation implements Exception {
  QuantContractViolation(this.message);
  final String message;
  @override
  String toString() => 'QuantContractViolation: $message';
}

class QuantSchemaValidator {
  QuantSchemaValidator(this.document);
  final Map<String, dynamic> document;

  void validate(String definition, dynamic value) {
    _check(document[r'$defs'][definition] as Map<String, dynamic>, value);
    _semantic(definition, value);
  }

  Never _fail(String message) => throw QuantContractViolation(message);

  void _check(Map<String, dynamic> schema, dynamic value) {
    const keywords = {
      r'$ref',
      'type',
      'properties',
      'required',
      'additionalProperties',
      'items',
      'pattern',
      'minLength',
      'minimum',
      'maximum',
      'const',
      'enum'
    };
    if (schema.keys.any((key) => !keywords.contains(key))) {
      _fail('Unsupported schema keyword');
    }
    if (schema.containsKey(r'$ref')) {
      final name = (schema[r'$ref'] as String).replaceFirst(r'#/$defs/', '');
      validate(name, value);
      return;
    }
    if (schema.containsKey('const')) {
      final expected = schema['const'];
      if (value != expected || (expected is int && value is! int)) {
        _fail('Constant mismatch');
      }
    }
    if (schema.containsKey('enum') &&
        !(schema['enum'] as List).contains(value)) {
      _fail('Enum mismatch');
    }
    final type = schema['type'];
    final correct = switch (type) {
      null => true,
      'object' => value is Map<String, dynamic>,
      'array' => value is List,
      'string' => value is String,
      'integer' => value is int,
      'boolean' => value is bool,
      _ => false,
    };
    if (!correct) _fail('Expected $type');
    if (type == 'object') {
      final map = value as Map<String, dynamic>;
      final properties =
          (schema['properties'] ?? <String, dynamic>{}) as Map<String, dynamic>;
      for (final key in (schema['required'] ?? []) as List) {
        if (!map.containsKey(key)) _fail('Missing field $key');
      }
      for (final key in map.keys) {
        if (properties.containsKey(key)) {
          _check(properties[key] as Map<String, dynamic>, map[key]);
        } else if (schema['additionalProperties'] == false) {
          _fail('Unknown field $key');
        }
      }
    } else if (type == 'array') {
      for (final item in value as List) {
        _check(schema['items'] as Map<String, dynamic>, item);
      }
    } else if (type == 'string') {
      if ((value as String).length < (schema['minLength'] ?? 0)) {
        _fail('String too short');
      }
      if (schema.containsKey('pattern')) {
        final match = RegExp(schema['pattern'] as String).firstMatch(value);
        if (match == null || match.start != 0 || match.end != value.length) {
          _fail('Invalid string');
        }
        if ((schema['pattern'] as String).contains('[0-9]*)(\\.[0-9]+)?')) {
          _semantic('Decimal', value);
        }
      }
    } else if (type == 'integer') {
      if ((value as int) < (schema['minimum'] ?? -9007199254740991)) {
        _fail('Below minimum');
      }
      if (value > (schema['maximum'] ?? 9007199254740991)) {
        _fail('Above maximum');
      }
    }
  }

  void _semantic(String name, dynamic value) {
    if (name == 'Decimal' || name == 'NonNegativeDecimal') {
      final text = value as String;
      final parts = text.replaceFirst('-', '').split('.');
      final digits = parts.join().replaceFirst(RegExp(r'^0+'), '');
      final scale = parts.length == 2 ? parts[1].length : 0;
      final adjusted = digits.isEmpty ? -scale : digits.length - scale - 1;
      if (digits.length > 34 || adjusted.abs() > 6144) {
        _fail('Decimal exceeds decimal128 domain');
      }
    } else if (name == 'Timestamp') {
      final parsed = DateTime.tryParse(value as String);
      if (parsed == null ||
          parsed.year < 1 ||
          parsed.toUtc().toIso8601String().substring(0, 19) !=
              value.substring(0, 19)) {
        _fail('Invalid calendar timestamp');
      }
    } else if (name == 'Account') {
      final cash = value['cash'] as String;
      final reserved = value['reserved_cash'] as String;
      final available = value['available_cash'] as String;
      final scale = [cash, reserved, available]
          .map((text) => text.contains('.') ? text.split('.')[1].length : 0)
          .reduce((a, b) => a > b ? a : b);
      BigInt scaled(String text) {
        final parts = text.split('.');
        final currentScale = parts.length == 2 ? parts[1].length : 0;
        return BigInt.parse(parts.join()) *
            BigInt.from(10).pow(scale - currentScale);
      }

      if (scaled(cash) - scaled(reserved) != scaled(available)) {
        _fail('Cash reservation invariant failed');
      }
      if (_compare(cash, '0') < 0 || _compare(available, '0') < 0) {
        _fail('Cash account cannot borrow');
      }
    } else if (name == 'Strategy') {
      final path = value['entrypoint']['file'] as String;
      if (path
          .split('/')
          .any((part) => part.isEmpty || part == '.' || part == '..')) {
        _fail('Entrypoint must be a normalized relative path');
      }
      final capabilities = value['requested_capabilities'] as List;
      if (capabilities.toSet().length != capabilities.length) {
        _fail('Duplicate capabilities');
      }
      void noFloat(dynamic item) {
        if (item is double) _fail('Floating strategy parameters are forbidden');
        if (item is int &&
            (item < -9007199254740991 || item > 9007199254740991)) {
          _fail('Integer exceeds interoperable range');
        }
        if (item is Map) item.values.forEach(noFloat);
        if (item is List) item.forEach(noFloat);
      }

      noFloat(value['parameters']);
    } else if (name == 'Instrument') {
      for (final field in ['price_step', 'quantity_step', 'money_step']) {
        if (_compare(value[field], '0') <= 0) _fail('Steps must be positive');
      }
    } else if (name == 'Dataset') {
      if (!DateTime.parse(value['first_open'])
          .isBefore(DateTime.parse(value['last_close']))) {
        _fail('Dataset interval must increase');
      }
    } else if (name == 'ProtectionGroup') {
      if (_compare(value['quantity'], '0') <= 0 ||
          (!value.containsKey('stop_price') &&
              !value.containsKey('take_price'))) {
        _fail('Protection needs quantity and trigger');
      }
      for (final field in ['stop_price', 'take_price']) {
        if (value.containsKey(field) && _compare(value[field], '0') <= 0) {
          _fail('Protection price must be positive');
        }
      }
    } else if (name == 'RunEvent') {
      validate(document['event_payloads'][value['kind']] as String,
          value['payload']);
    } else if (name == 'OrderState') {
      if (_compare(value['quantity'], '0') <= 0 ||
          _compare(value['filled_quantity'], value['quantity']) > 0) {
        _fail('Invalid order quantity');
      }
      if ((value['kind'] == 'limit') !=
          (value.containsKey('limit_price') as bool)) {
        _fail('Limit price mismatch');
      }
      if (value['status'] == 'filled' &&
          (_compare(value['quantity'], value['filled_quantity']) != 0 ||
              !value.containsKey('fill_price'))) {
        _fail('Filled order must have quantity and fill price');
      }
    } else if (name == 'ExitProtected') {
      if (_compare(value['params']['payload']['quantity'], '0') <= 0) {
        _fail('Exit quantity must be positive');
      }
    } else if (name == 'Position') {
      _semantic('Account', {
        'cash': value['quantity'],
        'reserved_cash': value['reserved_quantity'],
        'available_cash': value['available_quantity'],
      });
    } else if (name == 'Order') {
      if (_compare(value['quantity'], '0') <= 0) {
        _fail('Quantity must be positive');
      }
      if ((value['kind'] == 'limit') !=
          (value.containsKey('limit_price') as bool)) {
        _fail('Limit price must occur exactly for limit orders');
      }
      if (value.containsKey('limit_price') &&
          _compare(value['limit_price'], '0') <= 0) {
        _fail('Price must be positive');
      }
      if (value.containsKey('protection') && value['side'] != 'buy') {
        _fail('Only buys attach protection');
      }
    } else if (name == 'Protection') {
      if (_compare(value['stop_loss_percent'], '100') >= 0) {
        _fail('Stop loss must be below 100');
      }
    } else if (name == 'Bar') {
      for (final key in ['open', 'high', 'low', 'close']) {
        if (_compare(value[key], '0') <= 0 ||
            _compare(value['high'], value[key]) < 0 ||
            _compare(value['low'], value[key]) > 0) {
          _fail('Invalid positive OHLC range');
        }
      }
      if (!DateTime.parse(value['open_time'])
          .isBefore(DateTime.parse(value['close_time']))) {
        _fail('Bar interval must increase');
      }
    }
  }

  // Exact comparisons of canonical decimal strings; never convert to double.
  int _compare(String left, String right) {
    final a = left.split('.');
    final b = right.split('.');
    final scaleA = a.length == 2 ? a[1].length : 0;
    final scaleB = b.length == 2 ? b[1].length : 0;
    final scale = scaleA > scaleB ? scaleA : scaleB;
    final aa = BigInt.parse(a.join()) * BigInt.from(10).pow(scale - scaleA);
    final bb = BigInt.parse(b.join()) * BigInt.from(10).pow(scale - scaleB);
    return aa.compareTo(bb);
  }
}
