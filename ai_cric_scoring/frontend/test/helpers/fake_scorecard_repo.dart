import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:ai_cric_scoring/features/scorecard/data/models/match_scorecard.dart';
import 'package:ai_cric_scoring/features/scorecard/data/repositories/scorecard_repository.dart';

ScorecardTeam sampleScorecardTeam({
  String id = 'mt-a',
  String name = 'Weekend Warriors',
  String shortName = 'WW',
}) {
  return ScorecardTeam(matchTeamId: id, name: name, shortName: shortName);
}

MatchScorecard emptyScorecard({
  String matchId = 'match-ready',
  MatchStatus status = MatchStatus.ready,
}) {
  return MatchScorecard(
    match: ScorecardHeader(
      id: matchId,
      format: MatchFormat.t20,
      status: status,
      venueName: 'Central Ground',
      oversPerInnings: 20,
      ballsPerOver: 6,
      playersPerTeam: 11,
      teamA: sampleScorecardTeam(),
      teamB: sampleScorecardTeam(
        id: 'mt-b',
        name: 'Office XI',
        shortName: 'OXI',
      ),
    ),
    status: status,
  );
}

InningsScorecard sampleInnings({
  String id = 'innings-1',
  int number = 1,
  String status = 'LIVE',
  ScorecardTeam? battingTeam,
  ScorecardTeam? bowlingTeam,
  int runs = 12,
  int wickets = 1,
  int legalBalls = 7,
  String overs = '1.1',
  double runRate = 10.29,
  double? requiredRunRate,
  int? target,
  bool allOut = false,
  List<BattingRow>? batting,
  List<YetToBat>? yetToBat,
  List<BowlingRow>? bowling,
  List<FallOfWicket>? fallOfWickets,
  List<Partnership>? partnerships,
  List<OverSummary>? oversSummary,
  ExtrasBreakdown extras = const ExtrasBreakdown(
    total: 3,
    wides: 1,
    noBalls: 1,
    byes: 1,
    legByes: 0,
    penaltyRuns: 0,
  ),
}) {
  return InningsScorecard(
    id: id,
    number: number,
    status: status,
    battingTeam: battingTeam ?? sampleScorecardTeam(),
    bowlingTeam:
        bowlingTeam ??
        sampleScorecardTeam(id: 'mt-b', name: 'Office XI', shortName: 'OXI'),
    runs: runs,
    wickets: wickets,
    legalBalls: legalBalls,
    overs: overs,
    runRate: runRate,
    requiredRunRate: requiredRunRate,
    target: target,
    allOut: allOut,
    extras: extras,
    batting:
        batting ??
        const [
          BattingRow(
            matchPlayerId: 'mp-a-1',
            name: 'Rahul Shah',
            battingPosition: 1,
            runs: 5,
            balls: 4,
            fours: 1,
            sixes: 0,
            strikeRate: 125,
            status: 'OUT',
            dismissalText: 'b Dev Mehta',
          ),
          BattingRow(
            matchPlayerId: 'mp-a-2',
            name: 'Arjun Patel',
            battingPosition: 2,
            runs: 4,
            balls: 3,
            fours: 0,
            sixes: 0,
            strikeRate: 133.33,
            status: 'NOT_OUT',
            dismissalText: 'not out',
            isStriker: true,
          ),
        ],
    yetToBat:
        yetToBat ?? const [YetToBat(matchPlayerId: 'mp-a-3', name: 'Jay Shah')],
    bowling:
        bowling ??
        const [
          BowlingRow(
            matchPlayerId: 'mp-b-1',
            name: 'Dev Mehta',
            legalBalls: 7,
            overs: '1.1',
            maidens: 0,
            runsConceded: 11,
            wickets: 1,
            economy: 9.43,
            wides: 1,
            noBalls: 1,
          ),
        ],
    fallOfWickets:
        fallOfWickets ??
        const [
          FallOfWicket(
            wicketNumber: 1,
            score: 8,
            playerId: 'mp-a-1',
            playerName: 'Rahul Shah',
            legalBalls: 5,
            overs: '0.5',
          ),
        ],
    partnerships:
        partnerships ??
        const [
          Partnership(
            batter1Id: 'mp-a-1',
            batter1Name: 'Rahul Shah',
            batter2Id: 'mp-a-2',
            batter2Name: 'Arjun Patel',
            runs: 8,
            legalBalls: 5,
            startScore: 0,
            endScore: 8,
            isCurrent: false,
            batter1Runs: 5,
            batter2Runs: 3,
          ),
          Partnership(
            batter1Id: 'mp-a-2',
            batter1Name: 'Arjun Patel',
            batter2Id: 'mp-a-4',
            batter2Name: 'Kunal Mehta',
            runs: 4,
            legalBalls: 2,
            startScore: 8,
            endScore: 12,
            isCurrent: true,
            batter1Runs: 1,
            batter2Runs: 3,
          ),
        ],
    oversSummary:
        oversSummary ??
        const [
          OverSummary(
            overNumber: 1,
            runs: 10,
            wickets: 1,
            legalBalls: 6,
            isComplete: true,
            deliveries: [
              OverBall(label: '1', runs: 1, wicket: false, legal: true),
              OverBall(label: '4', runs: 4, wicket: false, legal: true),
              OverBall(label: 'WD', runs: 1, wicket: false, legal: false),
              OverBall(label: '2NB', runs: 3, wicket: false, legal: false),
              OverBall(label: 'W', runs: 0, wicket: true, legal: true),
              OverBall(label: '.', runs: 0, wicket: false, legal: true),
              OverBall(label: '2', runs: 2, wicket: false, legal: true),
            ],
          ),
        ],
  );
}

MatchScorecard liveScorecard({String matchId = 'match-ready'}) {
  return MatchScorecard(
    match: ScorecardHeader(
      id: matchId,
      format: MatchFormat.t20,
      status: MatchStatus.live,
      venueName: 'Central Ground',
      oversPerInnings: 20,
      ballsPerOver: 6,
      playersPerTeam: 11,
      teamA: sampleScorecardTeam(),
      teamB: sampleScorecardTeam(
        id: 'mt-b',
        name: 'Office XI',
        shortName: 'OXI',
      ),
    ),
    status: MatchStatus.live,
    currentInningsNumber: 1,
    innings: [sampleInnings()],
    summary: const ScorecardSummary(
      highestScorers: [
        NamedStat(matchPlayerId: 'mp-a-1', name: 'Rahul Shah', value: 5),
      ],
      mostWickets: [
        NamedStat(matchPlayerId: 'mp-b-1', name: 'Dev Mehta', value: 1),
      ],
      totalBoundaries: 1,
      totalSixes: 0,
      totalExtras: 3,
      largestPartnerships: [
        NamedStat(
          matchPlayerId: 'mp-a-1',
          name: 'Rahul Shah & Arjun Patel',
          value: 8,
        ),
      ],
    ),
  );
}

MatchScorecard completedScorecard({String matchId = 'match-ready'}) {
  final warriors = sampleScorecardTeam();
  final office = sampleScorecardTeam(
    id: 'mt-b',
    name: 'Office XI',
    shortName: 'OXI',
  );
  return MatchScorecard(
    match: ScorecardHeader(
      id: matchId,
      format: MatchFormat.t20,
      status: MatchStatus.completed,
      venueName: 'Central Ground',
      oversPerInnings: 20,
      ballsPerOver: 6,
      playersPerTeam: 11,
      teamA: warriors,
      teamB: office,
      resultType: 'WIN',
      winnerMatchTeamId: 'mt-a',
      winnerName: 'Weekend Warriors',
      marginRuns: 12,
    ),
    status: MatchStatus.completed,
    currentInningsNumber: 2,
    innings: [
      sampleInnings(
        id: 'innings-1',
        number: 1,
        status: 'COMPLETED',
        battingTeam: warriors,
        bowlingTeam: office,
        runs: 174,
        wickets: 7,
        legalBalls: 120,
        overs: '20.0',
        runRate: 8.7,
        batting: const [
          BattingRow(
            matchPlayerId: 'mp-a-1',
            name: 'Rahul Shah',
            battingPosition: 1,
            runs: 62,
            balls: 41,
            fours: 7,
            sixes: 2,
            strikeRate: 151.22,
            status: 'OUT',
            dismissalText: 'c Jay Shah b Dev Mehta',
          ),
          BattingRow(
            matchPlayerId: 'mp-a-2',
            name: 'Arjun Patel',
            battingPosition: 2,
            runs: 24,
            balls: 16,
            fours: 2,
            sixes: 1,
            strikeRate: 150,
            status: 'OUT',
            dismissalText: 'run out (Kunal Patel)',
          ),
        ],
        yetToBat: const [YetToBat(matchPlayerId: 'mp-a-3', name: 'Jay Shah')],
        bowling: const [
          BowlingRow(
            matchPlayerId: 'mp-b-1',
            name: 'Dev Mehta',
            legalBalls: 24,
            overs: '4.0',
            maidens: 0,
            runsConceded: 32,
            wickets: 2,
            economy: 8,
            wides: 2,
            noBalls: 1,
          ),
        ],
        extras: const ExtrasBreakdown(
          total: 14,
          wides: 5,
          noBalls: 2,
          byes: 3,
          legByes: 4,
          penaltyRuns: 0,
        ),
        fallOfWickets: const [
          FallOfWicket(
            wicketNumber: 1,
            score: 32,
            playerId: 'mp-a-1',
            playerName: 'Rahul Shah',
            legalBalls: 26,
            overs: '4.2',
          ),
        ],
        partnerships: const [
          Partnership(
            batter1Id: 'mp-a-1',
            batter1Name: 'Rahul Shah',
            batter2Id: 'mp-a-2',
            batter2Name: 'Arjun Patel',
            runs: 54,
            legalBalls: 38,
            startScore: 0,
            endScore: 54,
            isCurrent: false,
            batter1Runs: 30,
            batter2Runs: 24,
          ),
        ],
        oversSummary: const [
          OverSummary(
            overNumber: 1,
            runs: 7,
            wickets: 0,
            legalBalls: 6,
            isComplete: true,
            deliveries: [
              OverBall(label: '.', runs: 0, wicket: false, legal: true),
              OverBall(label: '1', runs: 1, wicket: false, legal: true),
              OverBall(label: '4', runs: 4, wicket: false, legal: true),
            ],
          ),
        ],
      ),
      sampleInnings(
        id: 'innings-2',
        number: 2,
        status: 'COMPLETED',
        battingTeam: office,
        bowlingTeam: warriors,
        runs: 162,
        wickets: 9,
        legalBalls: 120,
        overs: '20.0',
        runRate: 8.1,
        target: 175,
        extras: const ExtrasBreakdown(
          total: 6,
          wides: 2,
          noBalls: 1,
          byes: 2,
          legByes: 1,
          penaltyRuns: 0,
        ),
        batting: const [
          BattingRow(
            matchPlayerId: 'mp-b-2',
            name: 'Kunal Patel',
            battingPosition: 1,
            runs: 40,
            balls: 28,
            fours: 4,
            sixes: 1,
            strikeRate: 142.86,
            status: 'OUT',
            dismissalText: 'lbw b Rahul Shah',
          ),
        ],
        yetToBat: const [],
        bowling: const [
          BowlingRow(
            matchPlayerId: 'mp-a-1',
            name: 'Rahul Shah',
            legalBalls: 24,
            overs: '4.0',
            maidens: 1,
            runsConceded: 22,
            wickets: 3,
            economy: 5.5,
            wides: 0,
            noBalls: 0,
          ),
        ],
        fallOfWickets: const [],
        partnerships: const [],
        oversSummary: const [],
      ),
    ],
    summary: const ScorecardSummary(
      highestScorers: [
        NamedStat(matchPlayerId: 'mp-a-1', name: 'Rahul Shah', value: 62),
      ],
      mostWickets: [
        NamedStat(matchPlayerId: 'mp-a-1', name: 'Rahul Shah', value: 3),
      ],
      totalBoundaries: 16,
      totalSixes: 4,
      totalExtras: 20,
      largestPartnerships: [
        NamedStat(
          matchPlayerId: 'mp-a-1',
          name: 'Rahul Shah & Arjun Patel',
          value: 54,
        ),
      ],
    ),
  );
}

class FakeScorecardRepository implements ScorecardRepository {
  FakeScorecardRepository({
    this.scorecard,
    this.error,
    this.refreshError,
    this.pending,
  });

  MatchScorecard? scorecard;
  Object? error;
  Object? refreshError;
  Future<MatchScorecard>? pending;
  int calls = 0;

  @override
  Future<MatchScorecard> getScorecard(String matchId) async {
    calls += 1;
    if (pending != null && calls == 1) {
      return pending!;
    }
    if (calls > 1 && refreshError != null) {
      throw refreshError!;
    }
    if (error != null) {
      throw error!;
    }
    return scorecard ?? emptyScorecard(matchId: matchId);
  }
}

const scorecardNotFound = ApiException(
  'Match not found.',
  statusCode: 404,
  code: 'MATCH_NOT_FOUND',
);
