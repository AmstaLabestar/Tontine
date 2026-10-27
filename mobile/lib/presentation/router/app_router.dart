import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:tontine_app/presentation/screens/home/home_screen.dart';
import 'package:tontine_app/presentation/screens/members/members_screen.dart';
import 'package:tontine_app/presentation/screens/contributions/record_contribution_screen.dart';
import 'package:tontine_app/presentation/screens/history/history_screen.dart';
import 'package:tontine_app/presentation/screens/vault/vault_screen.dart';
import 'package:tontine_app/presentation/screens/sync/sync_screen.dart';
import 'package:tontine_app/presentation/screens/settings/settings_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
      GoRoute(path: '/members', builder: (context, state) => const MembersScreen()),
      GoRoute(path: '/record', builder: (context, state) => const RecordContributionScreen()),
      GoRoute(path: '/history', builder: (context, state) => const HistoryScreen()),
      GoRoute(path: '/vault', builder: (context, state) => const VaultScreen()),
      GoRoute(path: '/sync', builder: (context, state) => const SyncScreen()),
      GoRoute(path: '/settings', builder: (context, state) => const SettingsScreen()),
    ],
  );
});
