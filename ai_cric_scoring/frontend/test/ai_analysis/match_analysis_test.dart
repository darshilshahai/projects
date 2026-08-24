import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/core/theme/theme_mode_controller.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/fake_analysis_repo.dart';
import '../helpers/fake_match_repo.dart';
import '../helpers/pump_app.dart';

MatchDetail _completed({String id = 'match-done'}) {
  return sampleMatch(
    id: id,
    name: 'Sunday Final',
    status: MatchStatus.completed,
    format: MatchFormat.t20,
    venueName: 'Central Ground',
    completedAt: DateTime.utc(2026, 8, 12, 13),
    teams: [
      sampleMatchTeam(
        id: 'mt-a-$id',
        teamId: 'team-1',
        side: MatchSide.teamA,
        name: 'Weekend Warriors',
      ),
      sampleMatchTeam(
        id: 'mt-b-$id',
        teamId: 'team-2',
        side: MatchSide.teamB,
        name: 'Office XI',
      ),
    ],
    result: const MatchResultSummary(
      type: MatchResultType.won,
      winnerMatchTeamId: 'mt-a-match-done',
      winnerName: 'Weekend Warriors',
      marginRuns: 12,
      summary: 'Weekend Warriors won by 12 runs',
    ),
  );
}

MatchDetail _status(MatchStatus status) {
  return sampleMatch(
    id: 'match-${status.apiValue.toLowerCase()}',
    status: status,
    teams: [
      sampleMatchTeam(
        id: 'mt-a',
        teamId: 'team-1',
        side: MatchSide.teamA,
        name: 'A',
      ),
      sampleMatchTeam(
        id: 'mt-b',
        teamId: 'team-2',
        side: MatchSide.teamB,
        name: 'B',
      ),
    ],
  );
}

Future<void> _open(WidgetTester tester, String location) async {
  final context = tester.element(find.byType(Navigator).first);
  GoRouter.of(context).go(location);
  await tester.pumpAndSettle();
}

void main() {
  testWidgets('completed match detail shows generate AI analysis CTA', (
    tester,
  ) async {
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
    );
    await _open(tester, AppRoutes.match('match-done'));
    await tester.scrollUntilVisible(
      find.byKey(const Key('generate-ai-analysis')),
      200,
    );
    expect(find.byKey(const Key('generate-ai-analysis')), findsOneWidget);
    expect(find.byKey(const Key('view-ai-analysis')), findsNothing);
  });

  testWidgets('completed match detail shows view CTA when analysis exists', (
    tester,
  ) async {
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      analysis: FakeMatchAnalysisRepository(analysis: sampleAnalysis()),
    );
    await _open(tester, AppRoutes.match('match-done'));
    await tester.scrollUntilVisible(
      find.byKey(const Key('view-ai-analysis')),
      200,
    );
    expect(find.byKey(const Key('view-ai-analysis')), findsOneWidget);
  });

  testWidgets('non-completed matches do not show AI analysis CTA', (
    tester,
  ) async {
    for (final status in [
      MatchStatus.draft,
      MatchStatus.ready,
      MatchStatus.live,
    ]) {
      await pumpCricketApp(
        tester,
        matches: FakeMatchRepository(matches: [_status(status)]),
      );
      await _open(
        tester,
        AppRoutes.match('match-${status.apiValue.toLowerCase()}'),
      );
      expect(find.byKey(const Key('generate-ai-analysis')), findsNothing);
      expect(find.byKey(const Key('view-ai-analysis')), findsNothing);
    }
  });

  testWidgets('analysis screen not-generated and generating states', (
    tester,
  ) async {
    final repo = FakeMatchAnalysisRepository(
      generateDelay: const Duration(milliseconds: 80),
    );
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      analysis: repo,
    );
    await _open(tester, AppRoutes.matchAnalysis('match-done'));
    expect(find.text('No analysis yet'), findsOneWidget);
    await tester.tap(find.byKey(const Key('generate-analysis')));
    await tester.pump();
    expect(find.byKey(const Key('analyzing-match')), findsOneWidget);
    expect(find.text('ANALYZING MATCH'), findsOneWidget);
    await tester.pumpAndSettle();
    expect(
      find.text("Warriors' middle-order partnership decides tight chase"),
      findsWidgets,
    );
    expect(repo.generateCalls, 1);
  });

  testWidgets('analysis screen renders grounded sections and POTM', (
    tester,
  ) async {
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      analysis: FakeMatchAnalysisRepository(analysis: sampleAnalysis()),
    );
    await _open(tester, AppRoutes.matchAnalysis('match-done'));
    expect(find.text('WHY THEY WON'), findsOneWidget);
    expect(find.text('MIDDLE-ORDER STABILITY'), findsOneWidget);
    expect(find.text('WHERE THE MATCH SLIPPED'), findsOneWidget);
    expect(find.text('TURNING POINTS'), findsOneWidget);
    expect(find.text('AI PLAYER OF THE MATCH'), findsOneWidget);
    expect(find.text('AI RECOMMENDATION'), findsOneWidget);
    expect(find.text('RAHUL SHAH'), findsWidgets);
    expect(find.text('RECOMMENDATIONS'), findsOneWidget);
    expect(find.textContaining('68 RUNS'), findsWidgets);
  });

  testWidgets('generation error keeps scorecard facts intact messaging', (
    tester,
  ) async {
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      analysis: FakeMatchAnalysisRepository(
        generateError: analysisUnavailable(),
      ),
    );
    await _open(tester, AppRoutes.matchAnalysis('match-done'));
    await tester.tap(find.byKey(const Key('generate-analysis')));
    await tester.pumpAndSettle();
    expect(find.text('Analysis unavailable'), findsOneWidget);
    expect(find.textContaining('The match data is safe'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('regenerate confirms and replaces analysis', (tester) async {
    final repo = FakeMatchAnalysisRepository(analysis: sampleAnalysis());
    await pumpCricketApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      analysis: repo,
    );
    await _open(tester, AppRoutes.matchAnalysis('match-done'));
    await tester.tap(find.byKey(const Key('regenerate-analysis')));
    await tester.pumpAndSettle();
    expect(find.textContaining('different interpretation'), findsOneWidget);
    await tester.tap(find.byKey(const Key('confirm-regenerate')));
    await tester.pumpAndSettle();
    expect(find.text('Regenerated grounded headline'), findsWidgets);
    expect(repo.regenerateCalls, 1);
  });

  testWidgets('analysis screen supports light and dark themes', (tester) async {
    for (final mode in [ThemeMode.light, ThemeMode.dark]) {
      await pumpCricketApp(
        tester,
        matches: FakeMatchRepository(matches: [_completed()]),
        analysis: FakeMatchAnalysisRepository(analysis: sampleAnalysis()),
        overrides: [themeModeProvider.overrideWith(() => _FixedTheme(mode))],
      );
      await _open(tester, AppRoutes.matchAnalysis('match-done'));
      expect(find.text('AI / POST MATCH'), findsOneWidget);
      expect(find.text('AI PLAYER OF THE MATCH'), findsOneWidget);
    }
  });
}

class _FixedTheme extends ThemeModeController {
  _FixedTheme(this._mode);
  final ThemeMode _mode;
  @override
  ThemeMode build() => _mode;
}
