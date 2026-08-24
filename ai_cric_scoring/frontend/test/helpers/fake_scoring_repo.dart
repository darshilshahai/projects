import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:ai_cric_scoring/features/scoring/data/models/live_match_state.dart';
import 'package:ai_cric_scoring/features/scoring/data/repositories/scoring_repository.dart';

LiveMatchState sampleLiveState({
  String matchId = 'match-ready',
  MatchStatus status = MatchStatus.live,
  int revision = 1,
  int runs = 0,
  int wickets = 0,
  String overs = '0.0',
  double? crr,
  int? target,
  int? requiredRuns,
  double? rrr,
  int? ballsRemaining,
  bool needsNewBatter = false,
  bool needsNewBowler = false,
  bool needsOpeners = false,
  String? pendingInningsId,
  int? chaseTarget,
  String? resultType,
  String? winnerMatchTeamId,
  int? marginWickets,
  int? marginRuns,
  List<OverDelivery> currentOver = const [],
  List<LiveBatterOption> availableBatters = const [],
  List<LiveBowlerOption> availableBowlers = const [],
  LiveBatter? striker,
  LiveBatter? nonStriker,
  LiveBowler? bowler,
  int inningsNumber = 1,
}) {
  return LiveMatchState(
    matchId: matchId,
    status: status,
    revision: revision,
    innings: LiveInnings(
      id: 'innings-1',
      number: inningsNumber,
      status: status == MatchStatus.completed && !needsOpeners
          ? 'COMPLETED'
          : needsOpeners
          ? 'COMPLETED'
          : 'LIVE',
      battingTeam: const LiveTeam(
        matchTeamId: 'mt-a',
        name: 'Weekend Warriors',
      ),
      bowlingTeam: const LiveTeam(matchTeamId: 'mt-b', name: 'Office XI'),
      runs: runs,
      wickets: wickets,
      legalBalls: 0,
      overs: overs,
      ballsRemaining: ballsRemaining,
      currentRunRate: crr,
      target: target,
      requiredRuns: requiredRuns,
      requiredRunRate: rrr,
    ),
    striker:
        striker ??
        const LiveBatter(
          matchPlayerId: 'mp-a-1',
          name: 'Rahul Shah',
          runs: 0,
          balls: 0,
          fours: 0,
          sixes: 0,
          isStriker: true,
        ),
    nonStriker:
        nonStriker ??
        const LiveBatter(
          matchPlayerId: 'mp-a-2',
          name: 'Arjun Patel',
          runs: 0,
          balls: 0,
          fours: 0,
          sixes: 0,
        ),
    bowler:
        bowler ??
        const LiveBowler(
          matchPlayerId: 'mp-b-1',
          name: 'Dev Mehta',
          overs: '0.0',
          legalBalls: 0,
          runs: 0,
          wickets: 0,
        ),
    currentOver: currentOver,
    needsNewBatter: needsNewBatter,
    needsNewBowler: needsNewBowler,
    needsOpeners: needsOpeners,
    pendingInningsId: pendingInningsId,
    chaseTarget: chaseTarget,
    availableBatters: availableBatters,
    availableBowlers: availableBowlers,
    resultType: resultType,
    winnerMatchTeamId: winnerMatchTeamId,
    marginWickets: marginWickets,
    marginRuns: marginRuns,
  );
}

class RecordedScoringCall {
  const RecordedScoringCall({
    required this.method,
    required this.clientEventId,
    this.payload,
  });

  final String method;
  final String clientEventId;
  final Object? payload;
}

class FakeScoringRepository implements ScoringRepository {
  FakeScoringRepository({
    LiveMatchState? live,
    this.getLiveError,
    this.alreadyStarted = false,
  }) : live = live ?? sampleLiveState();

  LiveMatchState live;
  LiveMatchState? nextLive;
  ApiException? nextError;
  ApiException? getLiveError;
  int failTimes = 0;
  bool alreadyStarted;
  final List<RecordedScoringCall> calls = [];

  @override
  Future<LiveMatchState> getLive(String matchId) async {
    if (getLiveError != null) {
      throw getLiveError!;
    }
    return live;
  }

  @override
  Future<LiveMatchState> startMatch(
    String matchId,
    StartMatchRequest request,
  ) async {
    calls.add(
      RecordedScoringCall(
        method: 'startMatch',
        clientEventId: request.clientEventId,
        payload: request,
      ),
    );
    if (alreadyStarted) {
      throw const ApiException(
        'This match has already started.',
        statusCode: 409,
        code: 'MATCH_NOT_READY',
      );
    }
    return _complete('startMatch', request.clientEventId, request);
  }

  @override
  Future<LiveMatchState> startInnings(
    String matchId,
    String inningsId,
    StartMatchRequest request,
  ) {
    calls.add(
      RecordedScoringCall(
        method: 'startInnings',
        clientEventId: request.clientEventId,
        payload: request,
      ),
    );
    return _complete('startInnings', request.clientEventId, request);
  }

  @override
  Future<LiveMatchState> recordEvent(
    String matchId,
    ScoringEventRequest request,
  ) {
    calls.add(
      RecordedScoringCall(
        method: 'recordEvent',
        clientEventId: request.clientEventId,
        payload: request,
      ),
    );
    return _complete('recordEvent', request.clientEventId, request);
  }

  @override
  Future<LiveMatchState> selectBatter(
    String matchId,
    SelectPlayerRequest request,
  ) {
    calls.add(
      RecordedScoringCall(
        method: 'selectBatter',
        clientEventId: request.clientEventId,
        payload: request,
      ),
    );
    return _complete('selectBatter', request.clientEventId, request);
  }

  @override
  Future<LiveMatchState> selectBowler(
    String matchId,
    SelectPlayerRequest request,
  ) {
    calls.add(
      RecordedScoringCall(
        method: 'selectBowler',
        clientEventId: request.clientEventId,
        payload: request,
      ),
    );
    return _complete('selectBowler', request.clientEventId, request);
  }

  @override
  Future<LiveMatchState> undo(String matchId, UndoScoringRequest request) {
    calls.add(
      RecordedScoringCall(
        method: 'undo',
        clientEventId: request.clientEventId,
        payload: request,
      ),
    );
    return _complete('undo', request.clientEventId, request);
  }

  Future<LiveMatchState> _complete(
    String method,
    String clientEventId,
    Object payload,
  ) async {
    if (failTimes > 0) {
      failTimes -= 1;
      throw const ApiException('The request timed out.');
    }
    if (nextError != null) {
      final error = nextError!;
      nextError = null;
      throw error;
    }
    final result = nextLive ?? live.copyWith(revision: live.revision + 1);
    nextLive = null;
    live = result;
    return result;
  }
}
