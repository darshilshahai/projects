import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/core/routing/app_routes.dart';
import 'package:ai_cric_scoring/core/theme/theme_mode_controller.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:ai_cric_scoring/features/scoring/data/models/live_match_state.dart';
import 'package:ai_cric_scoring/features/scoring/presentation/controllers/live_scoring_controller.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:go_router/go_router.dart';

import '../helpers/fake_match_repo.dart';
import '../helpers/fake_scoring_repo.dart';
import '../helpers/pump_app.dart';

MatchPlayer _mp({
  required String id,
  required String name,
  bool keeper = false,
  bool captain = false,
}) {
  return MatchPlayer(
    id: id,
    playerId: 'p-$id',
    name: name,
    isPlaying: true,
    isCaptain: captain,
    isWicketKeeper: keeper,
  );
}

FakeMatchRepository _readyMatch({MatchStatus status = MatchStatus.ready}) {
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
              _mp(id: 'mp-a-1', name: 'Rahul Shah', captain: true),
              _mp(id: 'mp-a-2', name: 'Arjun Patel'),
              _mp(id: 'mp-a-3', name: 'Jay Shah'),
            ],
          ),
          sampleMatchTeam(
            id: 'mt-b',
            teamId: 'team-2',
            side: MatchSide.teamB,
            name: 'Office XI',
            players: [
              _mp(id: 'mp-b-1', name: 'Dev Mehta', keeper: true),
              _mp(id: 'mp-b-2', name: 'Kunal Patel'),
              _mp(id: 'mp-b-3', name: 'Sam Irani'),
            ],
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

void main() {
  test('parses live match state without calculating cricket values', () {
    final live = LiveMatchState.fromJson({
      'match_id': 'm1',
      'status': 'LIVE',
      'revision': 4,
      'innings': {
        'id': 'i1',
        'number': 2,
        'status': 'LIVE',
        'batting_team': {'match_team_id': 'mt-b', 'name': 'Office XI'},
        'bowling_team': {'match_team_id': 'mt-a', 'name': 'Weekend Warriors'},
        'runs': 35,
        'wickets': 1,
        'legal_balls': 18,
        'overs': '3.0',
        'balls_remaining': 12,
        'current_run_rate': 11.67,
        'target': 50,
        'required_runs': 15,
        'required_run_rate': 7.5,
      },
      'striker': {
        'match_player_id': 'mp-1',
        'name': 'Rahul Shah',
        'runs': 12,
        'balls': 8,
        'fours': 1,
        'sixes': 0,
        'strike_rate': 150.0,
        'is_striker': true,
      },
      'current_over': [
        {'label': '.', 'runs': 0, 'wicket': false, 'legal': true},
        {'label': '4NB', 'runs': 5, 'wicket': false, 'legal': false},
      ],
      'needs_new_batter': false,
      'chase_target': 50,
      'available_batters': [],
      'available_bowlers': [],
    });
    expect(live.revision, 4);
    expect(live.chaseTarget, 50);
    expect(live.innings?.ballsRemaining, 12);
    expect(live.innings?.requiredRunRate, 7.5);
    expect(live.currentOver.first.displayLabel, '•');
    expect(live.currentOver.last.displayLabel, 'NB+4');
  });

  testWidgets('READY match shows Start match and opening selectors', (
    tester,
  ) async {
    final scoring = FakeScoringRepository(
      getLiveError: const ApiException(
        'This match is not currently being scored.',
        statusCode: 409,
        code: 'MATCH_NOT_LIVE',
      ),
    );
    await pumpManagementApp(tester, matches: _readyMatch(), scoring: scoring);
    await _open(tester, AppRoutes.match('match-ready'));
    expect(find.byKey(const Key('start-scoring')), findsOneWidget);
    await tester.ensureVisible(find.byKey(const Key('start-scoring')));
    await tester.tap(find.byKey(const Key('start-scoring')));
    await tester.pumpAndSettle();
    expect(find.text('STRIKER'), findsOneWidget);
    expect(find.text('NON-STRIKER'), findsOneWidget);
    expect(find.text('OPENING BOWLER'), findsOneWidget);
  });

  testWidgets('opening validation blocks identical crease players', (
    tester,
  ) async {
    final scoring = FakeScoringRepository(
      getLiveError: const ApiException(
        'not live',
        statusCode: 409,
        code: 'MATCH_NOT_LIVE',
      ),
    );
    await pumpManagementApp(tester, matches: _readyMatch(), scoring: scoring);
    await _open(tester, AppRoutes.matchStart('match-ready'));
    await tester.tap(find.byKey(const Key('select-striker')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Rahul Shah'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('select-non-striker')));
    await tester.pumpAndSettle();
    expect(find.text('Rahul Shah'), findsWidgets);
    await tester.tap(find.text('Arjun Patel'));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('select-bowler')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Dev Mehta'));
    await tester.pumpAndSettle();
    scoring.nextLive = sampleLiveState(revision: 1);
    await tester.tap(find.byKey(const Key('confirm-start-match')));
    await tester.pumpAndSettle();
    expect(scoring.calls.single.method, 'startMatch');
    final request = scoring.calls.single.payload! as StartMatchRequest;
    expect(request.strikerId, 'mp-a-1');
    expect(request.nonStrikerId, 'mp-a-2');
    expect(request.bowlerId, 'mp-b-1');
    expect(find.byKey(const Key('run-4')), findsOneWidget);
  });

  testWidgets('run buttons submit canonical delivery payloads', (tester) async {
    final scoring = FakeScoringRepository(live: sampleLiveState());
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    expect(find.text('0/0'), findsOneWidget);
    for (final runs in [0, 1, 2, 3, 4, 5, 6]) {
      scoring.nextLive = sampleLiveState(revision: runs + 2, runs: runs);
      await tester.tap(find.byKey(Key('run-$runs')));
      await tester.pumpAndSettle();
      final call = scoring.calls.last;
      expect(call.method, 'recordEvent');
      final request = call.payload! as ScoringEventRequest;
      expect(request.delivery?.runsOffBat, runs);
      expect(request.baseRevision, greaterThan(0));
    }
  });

  testWidgets('one-tap wide and extras sheet submit facts only', (
    tester,
  ) async {
    final scoring = FakeScoringRepository(live: sampleLiveState());
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    scoring.nextLive = sampleLiveState(revision: 2, runs: 1);
    await tester.tap(find.byKey(const Key('extra-wide')));
    await tester.pumpAndSettle();
    final wide = scoring.calls.last.payload! as ScoringEventRequest;
    expect(wide.delivery?.wides, 1);
    expect(wide.delivery?.runsOffBat, 0);

    await tester.tap(find.byKey(const Key('extra-extras')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('BYE'));
    await tester.pumpAndSettle();
    scoring.nextLive = sampleLiveState(revision: 3, runs: 2);
    await tester.tap(find.byKey(const Key('record-extra')));
    await tester.pumpAndSettle();
    final extra = scoring.calls.last.payload! as ScoringEventRequest;
    expect(extra.delivery?.byes, 1);
  });

  testWidgets('wicket sheet requires fielder for caught only', (tester) async {
    final scoring = FakeScoringRepository(live: sampleLiveState());
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    await tester.tap(find.byKey(const Key('wicket-button')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('dismissal-BOWLED')));
    await tester.pumpAndSettle();
    expect(find.text('FIELDER'), findsNothing);
    scoring.nextLive = sampleLiveState(
      revision: 2,
      wickets: 1,
      needsNewBatter: true,
      availableBatters: const [
        LiveBatterOption(
          matchPlayerId: 'mp-a-3',
          name: 'Jay Shah',
          selectable: true,
          status: 'AVAILABLE',
        ),
        LiveBatterOption(
          matchPlayerId: 'mp-a-1',
          name: 'Rahul Shah',
          selectable: false,
          status: 'OUT',
        ),
      ],
    );
    await tester.tap(find.byKey(const Key('record-wicket')));
    await tester.pumpAndSettle();
    final request = scoring.calls.last.payload! as ScoringEventRequest;
    expect(request.delivery?.dismissal?.type, DismissalKind.bowled);
    expect(find.byKey(const Key('run-1')), findsNothing);
    expect(find.byKey(const Key('batter-mp-a-3')), findsOneWidget);
    scoring.nextLive = sampleLiveState(revision: 3, wickets: 1);
    await tester.tap(find.byKey(const Key('batter-mp-a-3')));
    await tester.pumpAndSettle();
    expect(scoring.calls.last.method, 'selectBatter');
    expect(find.byKey(const Key('run-1')), findsOneWidget);
  });

  testWidgets('needs_new_bowler blocks scoring until bowler selected', (
    tester,
  ) async {
    final scoring = FakeScoringRepository(
      live: sampleLiveState(
        needsNewBowler: true,
        availableBowlers: const [
          LiveBowlerOption(
            matchPlayerId: 'mp-b-2',
            name: 'Kunal Patel',
            selectable: true,
            overs: '0.0',
            legalBalls: 0,
            runs: 0,
            wickets: 0,
          ),
        ],
      ),
    );
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    expect(find.byKey(const Key('run-4')), findsNothing);
    expect(find.byKey(const Key('bowler-mp-b-2')), findsOneWidget);
    scoring.nextLive = sampleLiveState(revision: 8);
    await tester.tap(find.byKey(const Key('bowler-mp-b-2')));
    await tester.pumpAndSettle();
    expect(scoring.calls.last.method, 'selectBowler');
    expect(find.byKey(const Key('run-4')), findsOneWidget);
  });

  testWidgets('undo confirmation replaces canonical live state', (
    tester,
  ) async {
    final scoring = FakeScoringRepository(
      live: sampleLiveState(revision: 5, runs: 4),
    );
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    expect(find.text('4/0'), findsOneWidget);
    await tester.tap(find.byKey(const Key('undo-last')));
    await tester.pumpAndSettle();
    expect(find.text('Undo last delivery?'), findsOneWidget);
    scoring.nextLive = sampleLiveState(revision: 6, runs: 0);
    await tester.tap(find.byKey(const Key('confirm-accept')));
    await tester.pumpAndSettle();
    expect(scoring.calls.last.method, 'undo');
    expect(find.text('0/0'), findsOneWidget);
  });

  testWidgets('SCORE_CONFLICT reloads live state and does not replay', (
    tester,
  ) async {
    final scoring = FakeScoringRepository(live: sampleLiveState(revision: 2));
    scoring.nextError = const ApiException(
      'conflict',
      statusCode: 409,
      code: 'SCORE_CONFLICT',
      currentRevision: 9,
    );
    scoring.live = sampleLiveState(revision: 9, runs: 12);
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    await tester.tap(find.byKey(const Key('run-4')));
    await tester.pumpAndSettle();
    expect(
      scoring.calls.where((call) => call.method == 'recordEvent').length,
      1,
    );
    expect(find.text('12/0'), findsOneWidget);
    expect(
      find.text('Score changed on another session. Latest state loaded.'),
      findsOneWidget,
    );
  });

  testWidgets('timeout retry reuses the same client_event_id', (tester) async {
    var nextId = 0;
    final scoring = FakeScoringRepository(live: sampleLiveState(revision: 3));
    scoring.failTimes = 1;
    scoring.nextLive = sampleLiveState(revision: 4, runs: 4);
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
      overrides: [
        clientEventIdFactoryProvider.overrideWithValue(() {
          nextId += 1;
          return 'event-$nextId';
        }),
      ],
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    await tester.tap(find.byKey(const Key('run-4')));
    await tester.pumpAndSettle();
    final eventCalls = scoring.calls
        .where((call) => call.method == 'recordEvent')
        .toList();
    expect(eventCalls.length, 2);
    expect(eventCalls.first.clientEventId, eventCalls.last.clientEventId);
    expect(eventCalls.first.clientEventId, 'event-1');
    expect(find.text('4/0'), findsOneWidget);
  });

  testWidgets('innings complete then match complete states', (tester) async {
    final scoring = FakeScoringRepository(
      live: sampleLiveState(
        needsOpeners: true,
        pendingInningsId: 'innings-2',
        chaseTarget: 175,
        runs: 174,
        wickets: 7,
        overs: '20.0',
      ),
    );
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    expect(find.text('INNINGS COMPLETE'), findsOneWidget);
    expect(find.textContaining('175'), findsWidgets);
    expect(find.byKey(const Key('set-opening-batters')), findsOneWidget);
    expect(find.byKey(const Key('run-4')), findsNothing);
  });

  testWidgets('completed match shows result and hides scoring controls', (
    tester,
  ) async {
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.completed),
      scoring: FakeScoringRepository(
        live: sampleLiveState(
          status: MatchStatus.completed,
          resultType: 'WON',
          winnerMatchTeamId: 'mt-b',
          marginWickets: 4,
          runs: 175,
        ),
      ),
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    expect(find.byKey(const Key('view-match')), findsOneWidget);
    expect(find.byKey(const Key('run-4')), findsNothing);
    expect(find.textContaining('won by 4'), findsOneWidget);
  });

  testWidgets('phone and tablet scoring layouts exist', (tester) async {
    final scoring = FakeScoringRepository(live: sampleLiveState());
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: scoring,
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    expect(find.byKey(const Key('run-4')), findsOneWidget);
    expect(find.byKey(const Key('run-6')), findsOneWidget);
    expect(find.byKey(const Key('wicket-button')), findsOneWidget);
    expect(find.byType(VerticalDivider), findsNothing);

    await pumpManagementApp(
      tester,
      size: const Size(1024, 768),
      matches: _readyMatch(status: MatchStatus.live),
      scoring: FakeScoringRepository(live: sampleLiveState()),
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    expect(find.byKey(const Key('run-4')), findsOneWidget);
    expect(find.byType(VerticalDivider), findsOneWidget);
  });

  testWidgets('dark and light scoring screens render controls', (tester) async {
    for (final mode in [ThemeMode.dark, ThemeMode.light]) {
      await pumpManagementApp(
        tester,
        matches: _readyMatch(status: MatchStatus.live),
        scoring: FakeScoringRepository(live: sampleLiveState()),
        overrides: [themeModeProvider.overrideWith(() => _FixedTheme(mode))],
      );
      await _open(tester, AppRoutes.matchScoring('match-ready'));
      expect(find.byKey(const Key('run-0')), findsOneWidget);
      expect(find.byKey(const Key('wicket-button')), findsOneWidget);
      expect(find.byKey(const Key('undo-last')), findsOneWidget);
    }
  });

  testWidgets('run and wicket buttons expose semantics', (tester) async {
    final handle = tester.ensureSemantics();
    await pumpManagementApp(
      tester,
      matches: _readyMatch(status: MatchStatus.live),
      scoring: FakeScoringRepository(live: sampleLiveState()),
    );
    await _open(tester, AppRoutes.matchScoring('match-ready'));
    expect(
      tester.getSemantics(find.byKey(const Key('run-4'))).label,
      'Score 4 runs',
    );
    expect(
      tester.getSemantics(find.byKey(const Key('wicket-button'))).label,
      'Record wicket',
    );
    expect(
      tester.getSemantics(find.byKey(const Key('extra-wide'))).label,
      'Wide',
    );
    handle.dispose();
  });
}

class _FixedTheme extends ThemeModeController {
  _FixedTheme(this._mode);

  final ThemeMode _mode;

  @override
  ThemeMode build() => _mode;
}
