import 'package:ai_cric_scoring/features/analytics/data/models/historical_stats.dart';
import 'package:ai_cric_scoring/features/analytics/data/repositories/analytics_repository.dart';

const emptyOverview = AnalyticsOverview(
  completedMatches: 0,
  playerCount: 0,
  teamCount: 0,
);

BattingCareer sampleBatting({
  int matches = 8,
  int innings = 7,
  int runs = 312,
  int balls = 248,
  int notOuts = 1,
  int dismissals = 6,
  int? highestScore = 71,
  String? highestScoreDisplay = '71*',
  double? strikeRate = 125.81,
  double? battingAverage = 52.0,
}) {
  return BattingCareer(
    matches: matches,
    innings: innings,
    runs: runs,
    balls: balls,
    notOuts: notOuts,
    dismissals: dismissals,
    highestScore: highestScore,
    highestScoreDisplay: highestScoreDisplay,
    fours: 28,
    sixes: 9,
    strikeRate: strikeRate,
    battingAverage: battingAverage,
  );
}

BowlingCareer sampleBowling({
  int inningsBowled = 4,
  int wickets = 7,
  double? economy = 7.25,
  double? bowlingAverage = 18.4,
  String? bestBowling = '3/15',
  bool mixedRules = false,
}) {
  return BowlingCareer(
    matches: 8,
    inningsBowled: inningsBowled,
    legalBalls: 72,
    runsConceded: 87,
    wickets: wickets,
    wides: 3,
    noBalls: 1,
    oversDisplay: '12.0',
    economy: economy,
    bowlingAverage: bowlingAverage,
    bestBowling: bestBowling,
    mixedRules: mixedRules,
  );
}

PlayerCareerStats samplePlayerStats({
  String playerId = 'player-1',
  String name = 'Rahul Shah',
  BattingCareer? batting,
  BowlingCareer? bowling,
  bool smallSample = false,
}) {
  return PlayerCareerStats(
    playerId: playerId,
    name: name,
    isActive: true,
    scope: const HistoricalScope(description: 'Across 8 completed matches.'),
    batting: batting ?? sampleBatting(),
    bowling: bowling ?? sampleBowling(),
    recentForm: const [
      FormAppearance(matchId: 'match-done', display: '71*'),
      FormAppearance(matchId: 'match-2', display: '62'),
      FormAppearance(matchId: 'match-3', display: '18'),
    ],
    smallSample: smallSample,
  );
}

TeamHistoricalStats sampleTeamStats({
  String teamId = 'team-1',
  String name = 'Weekend Warriors',
  double? winPercentage = 60.0,
}) {
  return TeamHistoricalStats(
    teamId: teamId,
    name: name,
    isActive: true,
    scope: const HistoricalScope(description: 'Across 10 completed matches.'),
    matches: 10,
    wins: 6,
    losses: 3,
    ties: 1,
    winPercentage: winPercentage,
    averageRunsScored: 148.2,
    highestScore: 186,
    matchesChasing: 4,
    winsChasing: 2,
    matchesDefending: 6,
    winsDefending: 4,
    recentForm: const ['W', 'L', 'W', 'W', 'T'],
    recentMatches: const [
      FormAppearance(
        matchId: 'match-done',
        result: 'W',
        opponentName: 'Office XI',
      ),
    ],
    smallSample: false,
  );
}

AnalyticsOverview sampleOverview() {
  return AnalyticsOverview(
    completedMatches: 10,
    playerCount: 12,
    teamCount: 2,
    topRuns: const LeaderboardEntry(
      playerId: 'player-1',
      name: 'Rahul Shah',
      metric: 'runs',
      value: 312,
    ),
    topWickets: const LeaderboardEntry(
      playerId: 'player-2',
      name: 'Dev Patel',
      metric: 'wickets',
      value: 14,
    ),
    teamForm: const OverviewTeamForm(
      teamId: 'team-1',
      name: 'Weekend Warriors',
      results: ['W', 'L', 'W', 'W', 'T'],
      winPercentage: 60,
      matches: 10,
    ),
    suggestions: const [
      'Who has scored the most runs?',
      'Who has taken the most wickets?',
      'What is the team win rate?',
    ],
  );
}

HistoricalQueryAnswer sampleDirectAnswer({
  String content =
      'Rahul Shah has scored 312 runs in 7 innings at an average of 52.0.',
}) {
  return HistoricalQueryAnswer(
    content: content,
    answerType: 'DIRECT_STAT',
    questionType: 'PLAYER_STATS',
    evidence: const [
      HistoricalEvidence(
        factId: 'player_rahul_batting',
        type: 'batting',
        label: 'Batting',
        summary: '312 runs · 7 innings · avg 52.0',
      ),
    ],
  );
}

HistoricalQueryAnswer sampleAnalyticalAnswer() {
  return const HistoricalQueryAnswer(
    content: 'Warriors have won 3 of the last 5 matches in a small sample.',
    answerType: 'ANALYTICAL',
    questionType: 'TEAM_FORM',
    usedAi: true,
    evidence: [
      HistoricalEvidence(
        factId: 'team_ww_record',
        type: 'team',
        label: 'Weekend Warriors',
        summary: 'Weekend Warriors: 6/10 wins, win% 60.0',
      ),
    ],
  );
}

HistoricalQueryAnswer sampleClarificationAnswer() {
  return const HistoricalQueryAnswer(
    content:
        'I found more than one matching player: Rahul Shah and Rahul Patel. Which one do you mean?',
    answerType: 'CLARIFICATION',
    clarifications: [
      HistoricalClarification(
        label: 'Rahul Shah',
        message: 'I mean Rahul Shah.',
      ),
      HistoricalClarification(
        label: 'Rahul Patel',
        message: 'I mean Rahul Patel.',
      ),
    ],
  );
}

class FakeAnalyticsRepository implements AnalyticsRepository {
  FakeAnalyticsRepository({
    this.overviewData,
    this.player,
    this.team,
    this.playerCompare,
    this.teamCompare,
    this.answer,
    this.queryError,
    this.queryDelay = Duration.zero,
  });

  AnalyticsOverview? overviewData;
  PlayerCareerStats? player;
  TeamHistoricalStats? team;
  PlayerComparison? playerCompare;
  TeamComparison? teamCompare;
  HistoricalQueryAnswer? answer;
  Object? queryError;
  Duration queryDelay;
  int queryCalls = 0;
  String? lastQuestion;

  @override
  Future<AnalyticsOverview> overview(HistoricalFilter filter) async {
    return overviewData ?? emptyOverview;
  }

  @override
  Future<PlayerCareerStats> playerStats(
    String playerId,
    HistoricalFilter filter,
  ) async {
    return player ?? samplePlayerStats(playerId: playerId);
  }

  @override
  Future<TeamHistoricalStats> teamStats(
    String teamId,
    HistoricalFilter filter,
  ) async {
    return team ?? sampleTeamStats(teamId: teamId);
  }

  @override
  Future<PlayerComparison> comparePlayers({
    required String playerAId,
    required String playerBId,
    required HistoricalFilter filter,
  }) async {
    return playerCompare ??
        PlayerComparison(
          playerA: samplePlayerStats(playerId: playerAId, name: 'Rahul Shah'),
          playerB: samplePlayerStats(
            playerId: playerBId,
            name: 'Dev Patel',
            batting: sampleBatting(
              runs: 198,
              battingAverage: 33.0,
              strikeRate: 118.4,
            ),
            bowling: sampleBowling(inningsBowled: 0, wickets: 0),
          ),
          note: 'Each player\'s most recent 5 appearances.',
        );
  }

  @override
  Future<TeamComparison> compareTeams({
    required String teamAId,
    required String teamBId,
    required HistoricalFilter filter,
  }) async {
    return teamCompare ??
        TeamComparison(
          teamA: sampleTeamStats(teamId: teamAId),
          teamB: sampleTeamStats(
            teamId: teamBId,
            name: 'Office XI',
            winPercentage: 40,
          ),
          headToHead: const HeadToHead(
            matches: 4,
            teamAWins: 3,
            teamBWins: 1,
            ties: 0,
          ),
        );
  }

  @override
  Future<HistoricalQueryAnswer> query(String question) async {
    queryCalls += 1;
    lastQuestion = question;
    if (queryDelay > Duration.zero) {
      await Future<void>.delayed(queryDelay);
    }
    if (queryError != null) {
      throw queryError!;
    }
    return answer ?? sampleDirectAnswer();
  }
}
