import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/core/theme/theme_mode_controller.dart';
import 'package:ai_cric_scoring/features/home/presentation/screens/home_screen.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:ai_cric_scoring/features/matches/presentation/controllers/match_history_controller.dart';
import 'package:ai_cric_scoring/features/matches/presentation/controllers/match_providers.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/fake_management_repos.dart';
import '../helpers/fake_match_repo.dart';
import '../helpers/fake_scorecard_repo.dart';
import '../helpers/pump_app.dart';

MatchDetail _completed({
  String id = 'match-done',
  String name = 'Sunday Final',
  MatchFormat format = MatchFormat.t20,
  String teamA = 'Weekend Warriors',
  String teamB = 'Office XI',
  String? venueName = 'Central Ground',
  DateTime? completedAt,
  int aRuns = 174,
  int aWickets = 7,
  int bRuns = 162,
  int bWickets = 9,
  MatchResultSummary? result,
}) {
  final played = completedAt ?? DateTime.utc(2026, 8, 12, 13);
  return sampleMatch(
    id: id,
    name: name,
    status: MatchStatus.completed,
    format: format,
    venueName: venueName,
    completedAt: played,
    teams: [
      sampleMatchTeam(
        id: 'mt-a-$id',
        teamId: 'team-1',
        side: MatchSide.teamA,
        name: teamA,
      ),
      sampleMatchTeam(
        id: 'mt-b-$id',
        teamId: 'team-2',
        side: MatchSide.teamB,
        name: teamB,
      ),
    ],
    toss: MatchToss(winnerMatchTeamId: 'mt-b-$id', decision: TossDecision.bowl),
    result:
        result ??
        const MatchResultSummary(
          type: MatchResultType.won,
          winnerMatchTeamId: 'mt-a-match-done',
          winnerName: 'Weekend Warriors',
          marginRuns: 12,
          summary: 'Weekend Warriors won by 12 runs',
        ),
    innings: [
      InningsSummary(
        number: 1,
        battingMatchTeamId: 'mt-a-$id',
        battingTeamName: teamA,
        runs: aRuns,
        wickets: aWickets,
        legalBalls: 120,
        overs: '20.0',
      ),
      InningsSummary(
        number: 2,
        battingMatchTeamId: 'mt-b-$id',
        battingTeamName: teamB,
        runs: bRuns,
        wickets: bWickets,
        legalBalls: 120,
        overs: '20.0',
      ),
    ],
  );
}

List<MatchDetail> _archive(int count) {
  return [
    for (var index = 0; index < count; index++)
      _completed(
        id: 'hist-$index',
        name: 'Archive $index',
        format: index.isEven ? MatchFormat.t20 : MatchFormat.odi,
        completedAt: DateTime.utc(2026, 8, 1).add(Duration(hours: index)),
        result: MatchResultSummary(
          type: MatchResultType.won,
          winnerMatchTeamId: 'mt-a-hist-$index',
          winnerName: 'Weekend Warriors',
          marginRuns: 12,
          summary: 'Weekend Warriors won by 12 runs',
        ),
      ),
  ];
}

Future<void> _openHistory(WidgetTester tester) async {
  await tester.tap(find.byKey(const Key('nav-matches')));
  await tester.pumpAndSettle();
  await tester.tap(find.byKey(const Key('matches-tab-history')));
  await tester.pumpAndSettle();
}

class _FixedThemeMode extends ThemeModeController {
  _FixedThemeMode(this._mode);
  final ThemeMode _mode;
  @override
  ThemeMode build() => _mode;
}

void main() {
  testWidgets('empty history keeps search and filters visible', (tester) async {
    await pumpManagementApp(tester);
    await _openHistory(tester);
    expect(find.text('No history yet'), findsOneWidget);
    expect(
      find.text(
        'Completed matches will appear here with full scorecards and results.',
      ),
      findsOneWidget,
    );
    expect(find.byKey(const Key('history-search')), findsOneWidget);
    expect(find.byKey(const Key('history-filter')), findsOneWidget);
  });

  testWidgets('history list shows result rows from server text', (
    tester,
  ) async {
    await pumpManagementApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
    );
    await _openHistory(tester);
    expect(find.text('WEEKEND WARRIORS'), findsWidgets);
    expect(find.text('174/7'), findsOneWidget);
    expect(find.text('162/9'), findsOneWidget);
    expect(find.text('WEEKEND WARRIORS WON BY 12 RUNS'), findsOneWidget);
    expect(find.textContaining('12 AUG 2026'), findsOneWidget);
    expect(find.textContaining('CENTRAL GROUND'), findsOneWidget);
  });

  testWidgets('search empty state does not hide filters', (tester) async {
    await pumpManagementApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
    );
    await _openHistory(tester);
    await tester.enterText(find.byKey(const Key('history-search')), 'zzzz');
    await tester.pump(const Duration(milliseconds: 450));
    await tester.pumpAndSettle();
    expect(find.text('No matches found'), findsOneWidget);
    expect(find.byKey(const Key('history-search')), findsOneWidget);
    expect(find.byKey(const Key('history-filter')), findsOneWidget);
  });

  testWidgets('search finds a match by name', (tester) async {
    await pumpManagementApp(
      tester,
      matches: FakeMatchRepository(
        matches: [
          _completed(id: 'office', name: 'Office Cup'),
          _completed(id: 'sunday', name: 'Sunday Final'),
        ],
      ),
    );
    await _openHistory(tester);
    await tester.enterText(find.byKey(const Key('history-search')), 'Sunday');
    await tester.pump(const Duration(milliseconds: 450));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('history-row-sunday')), findsOneWidget);
    expect(find.byKey(const Key('history-row-office')), findsNothing);
  });

  testWidgets('filter replaces the list instead of appending', (tester) async {
    await pumpManagementApp(
      tester,
      teams: FakeTeamRepository(
        teams: [
          sampleTeam(id: 'team-1', name: 'Weekend Warriors'),
          sampleTeam(id: 'team-2', name: 'Office XI'),
        ],
      ),
      matches: FakeMatchRepository(
        matches: [
          _completed(id: 't20', name: 'T20 Cup', format: MatchFormat.t20),
          _completed(id: 'odi', name: 'ODI Cup', format: MatchFormat.odi),
        ],
      ),
    );
    await _openHistory(tester);
    expect(find.byKey(const Key('history-row-t20')), findsOneWidget);
    expect(find.byKey(const Key('history-row-odi')), findsOneWidget);
    await tester.tap(find.byKey(const Key('history-filter')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('ODI'));
    await tester.tap(find.byKey(const Key('apply-history-filters')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('history-row-odi')), findsOneWidget);
    expect(find.byKey(const Key('history-row-t20')), findsNothing);
  });

  testWidgets('tap completed match opens detail and scorecard', (tester) async {
    await pumpManagementApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      scorecard: FakeScorecardRepository(
        scorecard: completedScorecard(matchId: 'match-done'),
      ),
    );
    await _openHistory(tester);
    await tester.tap(find.byKey(const Key('history-row-match-done')));
    await tester.pumpAndSettle();
    expect(find.text('WEEKEND WARRIORS WON BY 12 RUNS'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.textContaining('elected to bowl'),
      200,
    );
    expect(find.text('CENTRAL GROUND'), findsWidgets);
    await tester.scrollUntilVisible(
      find.byKey(const Key('view-scorecard')),
      200,
    );
    expect(find.byKey(const Key('generate-ai-analysis')), findsOneWidget);
    await tester.tap(find.byKey(const Key('view-scorecard')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('scorecard-result')), findsOneWidget);
  });

  testWidgets('active tab still lists live ready and draft', (tester) async {
    await pumpManagementApp(
      tester,
      matches: FakeMatchRepository(
        matches: [
          sampleMatch(
            id: 'live',
            status: MatchStatus.live,
            teams: [
              sampleMatchTeam(
                id: 'l-a',
                teamId: 'team-1',
                side: MatchSide.teamA,
                name: 'Live A',
              ),
              sampleMatchTeam(
                id: 'l-b',
                teamId: 'team-2',
                side: MatchSide.teamB,
                name: 'Live B',
              ),
            ],
          ),
          sampleMatch(
            id: 'ready',
            status: MatchStatus.ready,
            teams: [
              sampleMatchTeam(
                id: 'r-a',
                teamId: 'team-1',
                side: MatchSide.teamA,
                name: 'Ready A',
              ),
              sampleMatchTeam(
                id: 'r-b',
                teamId: 'team-2',
                side: MatchSide.teamB,
                name: 'Ready B',
              ),
            ],
          ),
          sampleMatch(
            id: 'draft',
            status: MatchStatus.draft,
            teams: [
              sampleMatchTeam(
                id: 'd-a',
                teamId: 'team-1',
                side: MatchSide.teamA,
                name: 'Draft A',
              ),
              sampleMatchTeam(
                id: 'd-b',
                teamId: 'team-2',
                side: MatchSide.teamB,
                name: 'Draft B',
              ),
            ],
          ),
          _completed(id: 'done', name: 'Should hide'),
        ],
      ),
    );
    await tester.tap(find.byKey(const Key('nav-matches')));
    await tester.pumpAndSettle();
    expect(find.text('LIVE A'), findsOneWidget);
    expect(find.text('READY A'), findsOneWidget);
    expect(find.text('DRAFT A'), findsOneWidget);
    expect(find.text('SHOULD HIDE'), findsNothing);
  });

  testWidgets('history renders in light theme', (tester) async {
    await pumpManagementApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      overrides: [
        themeModeProvider.overrideWith(() => _FixedThemeMode(ThemeMode.light)),
      ],
    );
    await _openHistory(tester);
    expect(find.text('174/7'), findsOneWidget);
    await tester.tap(find.byKey(const Key('history-row-match-done')));
    await tester.pumpAndSettle();
    expect(find.text('WEEKEND WARRIORS WON BY 12 RUNS'), findsOneWidget);
  });

  testWidgets('history renders in dark theme', (tester) async {
    await pumpManagementApp(
      tester,
      matches: FakeMatchRepository(matches: [_completed()]),
      overrides: [
        themeModeProvider.overrideWith(() => _FixedThemeMode(ThemeMode.dark)),
      ],
    );
    await _openHistory(tester);
    expect(find.text('174/7'), findsOneWidget);
    await tester.tap(find.byKey(const Key('history-row-match-done')));
    await tester.pumpAndSettle();
    expect(find.text('WEEKEND WARRIORS WON BY 12 RUNS'), findsOneWidget);
  });

  testWidgets('tablet completed detail keeps scorecard action', (tester) async {
    await pumpManagementApp(
      tester,
      size: const Size(1024, 768),
      matches: FakeMatchRepository(matches: [_completed()]),
    );
    final context = tester.element(find.byType(HomeScreen));
    GoRouter.of(context).go(AppRoutes.match('match-done'));
    await tester.pumpAndSettle();
    expect(find.text('174/7'), findsOneWidget);
    expect(find.byKey(const Key('view-scorecard')), findsOneWidget);
    expect(find.textContaining('elected to bowl'), findsOneWidget);
  });

  test('history controller paginates without duplicates', () async {
    final repo = FakeMatchRepository(matches: _archive(30));
    final container = ProviderContainer(
      overrides: [matchRepositoryProvider.overrideWithValue(repo)],
    );
    addTearDown(container.dispose);
    container.listen(matchHistoryControllerProvider, (_, _) {});
    await container.read(matchHistoryControllerProvider.notifier).refresh();
    var state = container.read(matchHistoryControllerProvider);
    expect(state.items.length, 20);
    expect(state.total, 30);
    expect(state.hasMore, isTrue);
    await container.read(matchHistoryControllerProvider.notifier).loadMore();
    state = container.read(matchHistoryControllerProvider);
    expect(state.items.length, 30);
    expect(state.items.map((item) => item.id).toSet().length, 30);
    expect(state.hasMore, isFalse);
  });

  test('filter change replaces previous pages', () async {
    final repo = FakeMatchRepository(matches: _archive(25));
    final container = ProviderContainer(
      overrides: [matchRepositoryProvider.overrideWithValue(repo)],
    );
    addTearDown(container.dispose);
    container.listen(matchHistoryControllerProvider, (_, _) {});
    final controller = container.read(matchHistoryControllerProvider.notifier);
    await controller.refresh();
    await controller.loadMore();
    expect(container.read(matchHistoryControllerProvider).items.length, 25);
    await controller.applyFilters(
      const MatchHistoryFilters(format: MatchFormat.odi),
    );
    final state = container.read(matchHistoryControllerProvider);
    expect(state.items.every((item) => item.format == MatchFormat.odi), isTrue);
    expect(state.items.length, state.total);
    expect(state.items.any((item) => item.format == MatchFormat.t20), isFalse);
  });

  test('stale search response does not overwrite a newer query', () async {
    final repo = FakeMatchRepository(
      matches: [
        _completed(id: 'war', name: 'war only', teamA: 'Alpha', teamB: 'Beta'),
        _completed(
          id: 'warriors',
          name: 'warriors cup',
          teamA: 'Gamma',
          teamB: 'Delta',
        ),
      ],
    )..listDelay = const Duration(milliseconds: 80);
    final container = ProviderContainer(
      overrides: [matchRepositoryProvider.overrideWithValue(repo)],
    );
    addTearDown(container.dispose);
    container.listen(matchHistoryControllerProvider, (_, _) {});
    final controller = container.read(matchHistoryControllerProvider.notifier);
    await controller.refresh();
    controller.setSearch('war');
    await Future<void>.delayed(MatchHistoryController.searchDebounce);
    controller.setSearch('warriors');
    await Future<void>.delayed(MatchHistoryController.searchDebounce);
    await Future<void>.delayed(const Duration(milliseconds: 200));
    final state = container.read(matchHistoryControllerProvider);
    expect(state.search, 'warriors');
    expect(state.items.map((item) => item.id), ['warriors']);
  });

  test('page two failure keeps the first page', () async {
    final repo = FakeMatchRepository(matches: _archive(30))
      ..listMoreError = const ApiException('Unable to reach the backend.');
    final container = ProviderContainer(
      overrides: [matchRepositoryProvider.overrideWithValue(repo)],
    );
    addTearDown(container.dispose);
    container.listen(matchHistoryControllerProvider, (_, _) {});
    final controller = container.read(matchHistoryControllerProvider.notifier);
    await controller.refresh();
    await controller.loadMore();
    final state = container.read(matchHistoryControllerProvider);
    expect(state.items.length, 20);
    expect(state.loadMoreError, isNotNull);
  });
}
