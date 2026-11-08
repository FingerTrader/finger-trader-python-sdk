import 'dart:convert';

/// JSON decoder that preserves the protocol's duplicate-key rejection rule.
/// jsonDecode alone silently keeps the last duplicate member.
dynamic decodeQuantJson(String source) {
  var offset = 0;
  Never fail() => throw const FormatException('Invalid or duplicate JSON');
  void whitespace() {
    while (offset < source.length && ' \n\r\t'.contains(source[offset])) {
      offset++;
    }
  }

  String string() {
    if (offset >= source.length || source[offset] != '"') fail();
    final start = offset++;
    while (offset < source.length) {
      final char = source[offset++];
      if (char == '\\') {
        if (offset >= source.length) fail();
        offset++;
      } else if (char == '"') {
        return jsonDecode(source.substring(start, offset)) as String;
      }
    }
    fail();
  }

  late dynamic Function() value;
  value = () {
    whitespace();
    if (offset >= source.length) fail();
    final char = source[offset];
    if (char == '"') return string();
    if (char == '{') {
      offset++;
      final result = <String, dynamic>{};
      whitespace();
      if (offset < source.length && source[offset] == '}') {
        offset++;
        return result;
      }
      while (true) {
        whitespace();
        final key = string();
        if (result.containsKey(key)) fail();
        whitespace();
        if (offset >= source.length || source[offset++] != ':') fail();
        result[key] = value();
        whitespace();
        if (offset >= source.length) fail();
        final delimiter = source[offset++];
        if (delimiter == '}') return result;
        if (delimiter != ',') fail();
      }
    }
    if (char == '[') {
      offset++;
      final result = <dynamic>[];
      whitespace();
      if (offset < source.length && source[offset] == ']') {
        offset++;
        return result;
      }
      while (true) {
        result.add(value());
        whitespace();
        if (offset >= source.length) fail();
        final delimiter = source[offset++];
        if (delimiter == ']') return result;
        if (delimiter != ',') fail();
      }
    }
    final start = offset;
    while (offset < source.length && !' \n\r\t,]}'.contains(source[offset])) {
      offset++;
    }
    if (start == offset) fail();
    final token = source.substring(start, offset);
    if (RegExp(r'^-?(0|[1-9][0-9]*)$').hasMatch(token)) {
      final integer = BigInt.parse(token);
      if (integer.abs() > BigInt.from(9007199254740991)) fail();
    }
    final decoded = jsonDecode(token);
    if (decoded is double && !decoded.isFinite) fail();
    return decoded;
  };
  final result = value();
  whitespace();
  if (offset != source.length) fail();
  return result;
}
