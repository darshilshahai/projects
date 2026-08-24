import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/core/theme/theme_mode_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/fake_analytics_repo.dart';
import '../helpers/fake_management_repos.dart';
import '../helpers/pump_app.dart';

Future<void> _open(WidgetTester tester, String location) async {
  final context = tester.element(find.byType(Navigator).first);
  GoRouter.of(context).go(location);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('empty overview shows historical empty state', (tester) async {
    await pumpCricketApp(tester);
    await _open(tester, AppRoutes.stats);
    expect(find.byKey(const Key('stats-empty')), findsOneWidget);
    expect(find.text('No historical data yet'), findsOneWidget);
    expect(find.text('GO TO MATCHES'), findsOneWidget);
  });

  testWidgets('overview renders metrics from repository without client math', (
    tester,
  ) async {
    await pumpCricketApp(
      tester,
      analytics: FakeAnalyticsRepository(overviewData: sampleOverview()),
    );
    await _open(tester, AppRoutes.stats);
    expect(find.text('10'), findsWidgets);
    expect(find.text('Rahul Shah'), findsOneWidget);
    expect(find.text('Dev Patel'), findsOneWidget);
    expect(find.text('60.0%'), findsOneWidget);
    expect(find.byKey(const Key('open-historical-ask')), findsOneWidget);
  });

  testWidgets('player stats hide empty bowling and show form', (tester) async {
    await pumpCricketApp(
      tester,
      analytics: FakeAnalyticsRepository(
        player: samplePlayerStats(
          bowling: sampleBowling(inningsBowled: 0, wickets: 0),
        ),
      ),
    );
    await _open(tester, AppRoutes.statsPlayer('player-1'));
    expect(find.text('RAHUL SHAH'), findsWidgets);
    expect(find.text('52.00'), findsOneWidget);
    expect(find.text('71*'), findsWidgets);
    expect(find.text('BOWLING'), findsNothing);
  });

  testWidgets('team stats render win rate from repository', (tester) async {
    await pumpCricketApp(
      tester,
      analytics: FakeAnalyticsRepository(team: sampleTeamStats()),
    );
    await _open(tester, AppRoutes.statsTeam('team-1'));
    expect(find.text('WEEKEND WARRIORS'), findsWidgets);
    expect(find.text('60.0%'), findsOneWidget);
    expect(find.textContaining('CHASE'), findsOneWidget);
  });

  testWidgets('player compare shows unavailable bowling as dash', (
    tester,
  ) async {
    await pumpManagementApp(
      tester,
      players: FakePlayerRepository(
        players: [
          samplePlayer(id: 'player-1', name: 'Rahul Shah'),
          samplePlayer(id: 'player-2', name: 'Dev Patel'),
        ],
      ),
      analytics: FakeAnalyticsRepository(),
    );
    await _open(tester, AppRoutes.statsComparePlayers);
    await tester.tap(find.byKey(const Key('compare-player-a')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Rahul Shah').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('compare-player-b')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Dev Patel').last);
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('run-player-compare')));
    await tester.pumpAndSettle();
    expect(find.text('52.00'), findsOneWidget);
    expect(find.text('—'), findsWidgets);
  });

  testWidgets('ask shows suggestions then generating then evidence', (
    tester,
  ) async {
    final repo = FakeAnalyticsRepository(
      overviewData: sampleOverview(),
      queryDelay: const Duration(milliseconds: 80),
      answer: sampleAnalyticalAnswer(),
    );
    await pumpCricketApp(tester, analytics: repo);
    await _open(tester, AppRoutes.statsAsk);
    expect(find.text('TRY ASKING'), findsOneWidget);
    await tester.tap(find.byKey(const Key('hist-suggest-0')));
    await tester.pump();
    expect(find.byKey(const Key('analyzing-history')), findsOneWidget);
    await tester.pumpAndSettle();
    expect(find.textContaining('last 5 matches'), findsOneWidget);
    expect(find.text('EVIDENCE'), findsOneWidget);
    expect(repo.queryCalls, 1);
  });

  testWidgets('ask renders clarification chips and error retry', (
    tester,
  ) async {
    final repo = FakeAnalyticsRepository(answer: sampleClarificationAnswer());
    await pumpCricketApp(tester, analytics: repo);
    await _open(tester, AppRoutes.statsAsk);
    await tester.enterText(find.byKey(const Key('hist-ask-input')), 'Rahul?');
    await tester.tap(find.byKey(const Key('send-hist-ask')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('hist-clarify-Rahul Shah')), findsOneWidget);
    await tester.tap(find.byKey(const Key('hist-clarify-Rahul Shah')));
    await tester.pumpAndSettle();
    expect(repo.lastQuestion, 'I mean Rahul Shah.');
  });

  testWidgets('ask error shows retry', (tester) async {
    final repo = FakeAnalyticsRepository(
      queryError: const ApiException(
        'The analysis request timed out. Try again.',
        statusCode: 504,
      ),
    );
    await pumpCricketApp(tester, analytics: repo);
    await _open(tester, AppRoutes.statsAsk);
    await tester.enterText(
      find.byKey(const Key('hist-ask-input')),
      'Who leads runs?',
    );
    await tester.tap(find.byKey(const Key('send-hist-ask')));
    await tester.pumpAndSettle();
    expect(find.textContaining('timed out'), findsOneWidget);
  });

  testWidgets('stats screens support light, dark, phone and tablet', (
    tester,
  ) async {
    for (final mode in [ThemeMode.light, ThemeMode.dark]) {
      await pumpCricketApp(
        tester,
        size: const Size(1024, 768),
        analytics: FakeAnalyticsRepository(overviewData: sampleOverview()),
        overrides: [themeModeProvider.overrideWith(() => _FixedTheme(mode))],
      );
      await _open(tester, AppRoutes.stats);
      expect(find.text('Rahul Shah'), findsOneWidget);
      await _open(tester, AppRoutes.statsPlayer('player-1'));
      expect(find.text('52.00'), findsOneWidget);
    }
  });
}

class _FixedTheme extends ThemeModeController {
  _FixedTheme(this._mode);
  final ThemeMode _mode;
  @override
  ThemeMode build() => _mode;
}
