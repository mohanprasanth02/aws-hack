import 'package:flutter/foundation.dart';

class ApiConfig {
  static String? _customBaseUrl = 'https://aws-hack.onrender.com';

  /// Dynamically resolves the API host:
  /// - Default / Cloud Server: https://aws-hack.onrender.com
  /// - Supports runtime override
  static String get baseUrl {
    if (_customBaseUrl != null && _customBaseUrl!.isNotEmpty) {
      return _customBaseUrl!;
    }
    return 'https://aws-hack.onrender.com';
  }

  static set customBaseUrl(String? url) {
    if (url != null && url.trim().isNotEmpty) {
      String trimmed = url.trim();
      if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
        trimmed = 'http://$trimmed';
      }
      if (trimmed.endsWith('/')) {
        trimmed = trimmed.substring(0, trimmed.length - 1);
      }
      _customBaseUrl = trimmed;
    } else {
      _customBaseUrl = null;
    }
  }

  static String get loginEndpoint => '$baseUrl/api/worker/login';
  static String get tasksEndpoint => '$baseUrl/api/worker/tasks';
  static String get autoDispatchEndpoint => '$baseUrl/api/work-orders/auto-dispatch-risk';
  static String get resetEndpoint => '$baseUrl/api/work-orders/reset';
  
  static String updateStatusEndpoint(int orderId) => '$baseUrl/api/worker/tasks/$orderId/status';
  static String completeTaskEndpoint(int orderId) => '$baseUrl/api/worker/tasks/$orderId/complete';
  static String singleTaskEndpoint(int orderId) => '$baseUrl/api/worker/tasks/$orderId';
}
