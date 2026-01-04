import 'package:flutter/material.dart';
import 'package:flutter_riverpod/provider_scope.dart';
import 'core/theme.dart';
import 'features/auth/presentation/login_screen.dart';

void main() {
  runApp(const ProviderScope(child: EdukaApp()));
}

class EdukaApp extends StatelessWidget {
  const EdukaApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'eDuka Pro',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.darkTheme,
      home: const LoginScreen(),
    );
  }
}
