import 'dart:async';

import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/core/theme/theme_mode_controller.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:ai_cric_scoring/features/scorecard/data/models/match_scorecard.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/fake_match_repo.dart';
import '../helpers/fake_scorecard_repo.dart';
import '../helpers/fake_scoring_repo.dart';
import '../helpers/pump_app.dart';

MatchPlayer _mp({required String id, required String name}) {
  return MatchPlayer(
    id: id,
    playerId: 'p-$id',
    name: name,
    isPlaying: true,
    isCaptain: false,
    isWicketKeeper: false,
  );
}

FakeMatchRepository _match({MatchStatus status = MatchStatus.live}) {
  return FakeMatchRepository(
    matches: [
      sampleMatch(
        id: 'match-ready',
        status: status,
        teams: [
          sampleMatchTeam(
            id: 'mt-a',
            teamId: 'team-1',
            side: MatchSide.teamA,
            name: 'Weekend Warriors',
            players: [
              _mp(id: 'mp-a-1', name: 'Rahul Shah'),
              _mp(id: 'mp-a-2', name: 'Arjun Patel'),
            ],
          ),
          sampleMatchTeam(
            id: 'mt-b',
            teamId: 'team-2',
            side: MatchSide.teamB,
            name: 'Office XI',
            players: [_mp(id: 'mp-b-1', name: 'Dev Mehta')],
          ),
        ],
        toss: const MatchToss(
          winnerMatchTeamId: 'mt-a',
          decision: TossDecision.bat,
        ),
      ),
    ],
  );
}

Future<void> _open(WidgetTester tester, String location) async {
  final context = tester.element(find.byType(Navigator).first);
  GoRouter.of(context).go(location);
  await tester.pumpAndSettle();
}

Future<void> _reveal(WidgetTester tester, Finder finder) async {
  await tester.scrollUntilVisible(finder, 160);
  await tester.ensureVisible(finder);
  await tester.pumpAndSettle();
}

Future<void> _openScorecard(
  WidgetTester tester, {
  MatchScorecard? scorecard,
  FakeScorecardRepository? repo,
  MatchStatus matchStatus = MatchStatus.live,
  Size size = const Size(390, 844),
  List<Override> overrides = const [],
}) async {
  await pumpManagementApp(
    tester,
    size: size,
    matches: _match(status: matchStatus),
    scorecard: repo ?? FakeScorecardRepository(scorecard: scorecard),
    overrides: overrides,
  );
  await _open(tester, AppRoutes.matchScorecard('match-ready'));
}

void main() {
  test('parses scorecard facts without recalculating cricket values', () {
    final card = MatchScorecard.fromJson({
      'status': 'LIVE',
      'current_innings_number': 1,
      'match': {
        'id': 'm1',
        'format': 'T20',
        'status': 'LIVE',
        'venue_name': 'Central Ground',
        'overs_per_innings': 20,
        'balls_per_over': 6,
        'players_per_team': 11,
        'team_a': {
          'match_team_id': 'mt-a',
          'name': 'Weekend Warriors',
          'short_name': 'WW',
        },
        'team_b': {
          'match_team_id': 'mt-b',
          'name': 'Office XI',
          'short_name': 'OXI',
        },
        'result_type': 'WIN',
        'winner_name': 'Weekend Warriors',
        'margin_runs': 12,
      },
      'innings': [
        {
          'id': 'i1',
          'number': 1,
          'status': 'LIVE',
          'batting_team': {
            'match_team_id': 'mt-a',
            'name': 'Weekend Warriors',
            'short_name': 'WW',
          },
          'bowling_team': {
            'match_team_id': 'mt-b',
            'name': 'Office XI',
            'short_name': 'OXI',
          },
          'runs': 12,
          'wickets': 1,
          'legal_balls': 7,
          'overs': '1.1',
          'run_rate': 10.29,
          'required_run_rate': 8.5,
          'target': 50,
          'all_out': false,
          'extras': {
            'total': 3,
            'wides': 1,
            'no_balls': 1,
            'byes': 1,
            'leg_byes': 0,
            'penalty_runs': 0,
          },
          'batting': [
            {
              'match_player_id': 'mp-1',
              'name': 'Rahul Shah',
              'batting_position': 1,
              'runs': 5,
              'balls': 4,
              'fours': 1,
              'sixes': 0,
              'strike_rate': 125.0,
              'status': 'NOT_OUT',
              'dismissal_text': 'not out',
              'is_striker': true,
            },
          ],
          'overs_summary': [
            {
              'over_number': 1,
              'runs': 5,
              'wickets': 0,
              'legal_balls': 2,
              'is_complete': false,
              'deliveries': [
                {'label': '.', 'runs': 0, 'wicket': false, 'legal': true},
                {'label': '4NB', 'runs': 5, 'wicket': false, 'legal': false},
              ],
            },
          ],
        },
      ],
    });
    expect(card.match.title, 'Weekend Warriors vs Office XI');
    expect(card.match.resultLabel, 'WEEKEND WARRIORS WON BY 12 RUNS');
    expect(card.innings.first.scoreLine, '12/1');
    expect(card.innings.first.requiredRunRate, 8.5);
    expect(card.innings.first.batting.first.isStriker, isTrue);
    expect(
      card.innings.first.oversSummary.first.deliveries[0].displayLabel,
      '•',
    );
    expect(
      card.innings.first.oversSummary.first.deliveries[1].displayLabel,
      'NB+4',
    );
  });

  test('all-out score line uses team wickets, not a 10-wicket assumption', () {
    final innings = sampleInnings(runs: 74, wickets: 4, allOut: true);
    expect(innings.scoreLine, '74 ALL OUT');
  });

  testWidgets('loading state shows technical indicator', (tester) async {
    final pending = Completer<MatchScorecard>();
    await pumpManagementApp(
      tester,
      matches: _match(),
      scorecard: FakeScorecardRepository(pending: pending.future),
    );
    final context = tester.element(find.byType(Navigator).first);
    GoRouter.of(context).go(AppRoutes.matchScorecard('match-ready'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 20));
    expect(find.text('Loading scorecard'), findsOneWidget);
    pending.complete(liveScorecard());
    await tester.pumpAndSettle();
    expect(find.text('ARJUN PATEL *'), findsOneWidget);
  });

  testWidgets('error state offers retry without raw traces', (tester) async {
    await _openScorecard(
      tester,
      repo: FakeScorecardRepository(error: scorecardNotFound),
    );
    expect(find.text('Unable to load scorecard.'), findsOneWidget);
    expect(find.text('Retry'), findsOneWidget);
    expect(find.textContaining('MATCH_NOT_FOUND'), findsNothing);
  });

  testWidgets('ready match without innings shows empty state', (tester) async {
    await _openScorecard(
      tester,
      scorecard: emptyScorecard(),
      matchStatus: MatchStatus.ready,
    );
    expect(find.text('Scorecard not available'), findsOneWidget);
    expect(find.text('The match has not started yet.'), findsOneWidget);
    expect(find.byKey(const Key('batting-section')), findsNothing);
  });

  testWidgets('live scorecard renders current batters and sections', (
    tester,
  ) async {
    await _openScorecard(tester, scorecard: liveScorecard());
    expect(find.text('WEEKEND WARRIORS VS OFFICE XI'), findsOneWidget);
    expect(find.text('LIVE'), findsWidgets);
    expect(find.text('12/1'), findsWidgets);
    expect(find.text('RAHUL SHAH'), findsOneWidget);
    expect(find.text('ARJUN PATEL *'), findsOneWidget);
    expect(find.text('not out'), findsOneWidget);
    expect(find.text('b Dev Mehta'), findsOneWidget);
    expect(find.text('YET TO BAT'), findsOneWidget);
    expect(find.text('Jay Shah'), findsOneWidget);
    await _reveal(tester, find.byKey(const Key('extras-section')));
    expect(find.text('W 1 · NB 1 · B 1'), findsOneWidget);
    expect(find.byKey(const Key('total-section')), findsOneWidget);
    await _reveal(tester, find.byKey(const Key('fow-section')));
    expect(find.text('1-8'), findsOneWidget);
    await _reveal(tester, find.text('DEV MEHTA'));
    expect(find.text('WD 1 · NB 1'), findsOneWidget);
  });

  testWidgets('phone scorecard expands partnerships and overs', (tester) async {
    await _openScorecard(tester, scorecard: liveScorecard());
    expect(find.text('Rahul Shah + Arjun Patel'), findsNothing);
    await _reveal(tester, find.byKey(const Key('partnerships-section')));
    await tester.tap(find.byKey(const Key('partnerships-section')));
    await tester.pumpAndSettle();
    expect(find.text('CURRENT'), findsOneWidget);
    expect(find.text('Arjun Patel + Kunal Mehta'), findsOneWidget);
    await _reveal(tester, find.byKey(const Key('overs-section')));
    await tester.tap(find.byKey(const Key('overs-section')));
    await tester.pumpAndSettle();
    expect(find.text('OVER 1'), findsOneWidget);
    await tester.tap(find.text('OVER 1'));
    await tester.pumpAndSettle();
    expect(find.text('NB+2'), findsOneWidget);
    expect(find.text('•'), findsOneWidget);
  });

  testWidgets('completed scorecard shows result and innings switcher', (
    tester,
  ) async {
    await _openScorecard(
      tester,
      scorecard: completedScorecard(),
      matchStatus: MatchStatus.completed,
    );
    expect(find.byKey(const Key('scorecard-result')), findsOneWidget);
    expect(find.text('WEEKEND WARRIORS WON BY 12 RUNS'), findsOneWidget);
    expect(find.text('174/7'), findsWidgets);
    expect(find.text('c Jay Shah b Dev Mehta'), findsOneWidget);
    expect(find.text('DID NOT BAT'), findsOneWidget);
    expect(find.text('W 5 · NB 2 · B 3 · LB 4'), findsOneWidget);
    await tester.tap(find.textContaining('OXI'));
    await tester.pumpAndSettle();
    expect(find.text('162/9'), findsWidgets);
    expect(find.text('lbw b Rahul Shah'), findsOneWidget);
    expect(find.textContaining('TARGET 175'), findsOneWidget);
  });

  testWidgets('tablet uses table headers instead of stacked phone rows', (
    tester,
  ) async {
    await _openScorecard(
      tester,
      scorecard: completedScorecard(),
      matchStatus: MatchStatus.completed,
      size: const Size(1024, 768),
    );
    expect(find.text('Batter'), findsOneWidget);
    expect(find.text('RAHUL SHAH'), findsNothing);
    await _reveal(tester, find.text('Rahul Shah'));
    expect(find.text('Rahul Shah'), findsWidgets);
    await _reveal(tester, find.text('Bowler'));
    expect(find.text('Bowler'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('phone layout stays readable without overflow', (tester) async {
    await _openScorecard(tester, scorecard: completedScorecard());
    expect(find.byKey(const Key('batting-section')), findsOneWidget);
    await _reveal(tester, find.byKey(const Key('bowling-section')));
    expect(find.byKey(const Key('bowling-section')), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('dark and light scorecards render the same facts', (
    tester,
  ) async {
    for (final mode in [ThemeMode.dark, ThemeMode.light]) {
      await _openScorecard(
        tester,
        scorecard: liveScorecard(),
        overrides: [themeModeProvider.overrideWith(() => _FixedTheme(mode))],
      );
      expect(find.text('12/1'), findsWidgets);
      expect(find.text('ARJUN PATEL *'), findsOneWidget);
      expect(find.byKey(const Key('batting-section')), findsOneWidget);
    }
  });

  testWidgets('failed refresh keeps existing scorecard visible', (
    tester,
  ) async {
    await _openScorecard(
      tester,
      repo: FakeScorecardRepository(
        scorecard: liveScorecard(),
        refreshError: scorecardNotFound,
      ),
    );
    expect(find.text('12/1'), findsWidgets);
    await tester.tap(find.byKey(const Key('refresh-scorecard')));
    await tester.pumpAndSettle();
    expect(find.text('12/1'), findsWidgets);
    expect(find.text('Could not refresh.'), findsWidgets);
    expect(find.text('Unable to load scorecard.'), findsNothing);
  });

  testWidgets('match detail opens scorecard for a live match', (tester) async {
    await pumpManagementApp(
      tester,
      matches: _match(),
      scorecard: FakeScorecardRepository(scorecard: liveScorecard()),
    );
    await _open(tester, AppRoutes.match('match-ready'));
    await _reveal(tester, find.byKey(const Key('view-scorecard')));
    await tester.tap(find.byKey(const Key('view-scorecard')));
    await tester.pumpAndSettle();
    expect(find.text('SCORECARD'), findsOneWidget);
    expect(find.text('12/1'), findsWidgets);
  });

  testWidgets('completed match detail opens the scorecard', (tester) async {
    await pumpManagementApp(
      tester,
      matches: _match(status: MatchStatus.completed),
      scorecard: FakeScorecardRepository(scorecard: completedScorecard()),
    );
    await _open(tester, AppRoutes.match('match-ready'));
    expect(find.text('Scoring is closed for completed matches.'), findsNothing);
    await _reveal(tester, find.byKey(const Key('view-scorecard')));
    await tester.tap(find.byKey(const Key('view-scorecard')));
    await tester.pumpAndSettle();
    expect(find.text('WEEKEND WARRIORS WON BY 12 RUNS'), findsOneWidget);
  });

  testWidgets('live scoring overflow opens the scorecard', (tester) async {
    await pumpManagementApp(
      tester,
      matches: _match(),
      scoring: FakeScoringRepository(live: sampleLiveState()),
      scorecard: FakeScorecardRepository(scorecard: liveScorecard()),
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    await tester.tap(find.byKey(const Key('scoring-overflow')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('View scorecard'));
    await tester.pumpAndSettle();
    expect(find.text('SCORECARD'), findsOneWidget);
    expect(find.text('ARJUN PATEL *'), findsOneWidget);
  });
}

class _FixedTheme extends ThemeModeController {
  _FixedTheme(this._mode);

  final ThemeMode _mode;

  @override
  ThemeMode build() => _mode;
}
