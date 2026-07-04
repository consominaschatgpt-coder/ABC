import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiException implements Exception {
  final int statusCode;
  final Object? detail;

  ApiException(this.statusCode, this.detail);

  @override
  String toString() => 'ApiException($statusCode, $detail)';
}

/// Cliente HTTP para a API do backend (ver ../../backend/app/main.py).
/// Fica burro de proposito: nao decide o que fazer offline, so fala com a
/// rede quando chamado — quem decide se/quando chamar e o SyncEngine.
class ApiClient {
  final String baseUrl;
  final http.Client _client;
  String? _token;

  ApiClient({required this.baseUrl, http.Client? client}) : _client = client ?? http.Client();

  void setToken(String? token) {
    _token = token;
  }

  Map<String, String> _headers({bool withBody = false}) {
    final headers = <String, String>{};
    if (_token != null) headers['Authorization'] = 'Bearer $_token';
    if (withBody) headers['Content-Type'] = 'application/json';
    return headers;
  }

  Future<dynamic> _handle(http.Response response) {
    final isJson = response.headers['content-type']?.contains('application/json') ?? false;
    final decoded = isJson && response.body.isNotEmpty ? jsonDecode(response.body) : response.body;
    if (response.statusCode >= 400) {
      final detail = decoded is Map<String, dynamic> ? decoded['detail'] : decoded;
      throw ApiException(response.statusCode, detail);
    }
    return Future.value(decoded);
  }

  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    final uri = Uri.parse('$baseUrl$path').replace(queryParameters: query);
    final response = await _client.get(uri, headers: _headers());
    return _handle(response);
  }

  Future<dynamic> post(String path, {Object? body}) async {
    final uri = Uri.parse('$baseUrl$path');
    final response = await _client.post(
      uri,
      headers: _headers(withBody: true),
      body: body != null ? jsonEncode(body) : null,
    );
    return _handle(response);
  }

  Future<dynamic> patch(String path, {Object? body}) async {
    final uri = Uri.parse('$baseUrl$path');
    final response = await _client.patch(
      uri,
      headers: _headers(withBody: true),
      body: body != null ? jsonEncode(body) : null,
    );
    return _handle(response);
  }
}
