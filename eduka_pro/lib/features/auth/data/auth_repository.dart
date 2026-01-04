import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/api_service.dart';

class AuthRepository {
  final ApiService _apiService = ApiService();

  Future<bool> login(String username, String password) async {
    try {
      final response = await _apiService.post(
        'auth/login/',
        data: {'username': username, 'password': password},
      );

      if (response.statusCode == 200) {
        final access = response.data['access'];
        final refresh = response.data['refresh'];

        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', access);
        await prefs.setString('refresh_token', refresh);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
  }

  Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey('access_token');
  }
}
