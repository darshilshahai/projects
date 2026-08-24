import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/matches/data/models/match.dart';
import 'package:ai_cric_scoring/features/matches/data/repositories/match_repository.dart';
import 'package:ai_cric_scoring/features/teams/data/models/roster_member.dart';
import 'package:ai_cric_scoring/features/teams/data/models/team.dart';

MatchDetail sampleMatch({
  String id = 'match-1',
  MatchStatus status = MatchStatus.draft,
  MatchFormat format = MatchFormat.t20,
  String? name,
  String? venueName = 'Central Ground',
  int overs = 20,
  int playersPerTeam = 11,
  List<MatchTeam> teams = const [],
  MatchToss? toss,
  List<String> readinessIssues = const [],
  MatchResultSummary? result,
  List<InningsSummary> innings = const [],
  DateTime? completedAt,
}) {
  final now = DateTime.utc(2026, 8, 14, 10);
  return MatchDetail(
    id: id,
    name: name,
    format: format,
    status: status,
    venueName: venueName,
    oversPerInnings: overs,
    ballsPerOver: 6,
    playersPerTeam: playersPerTeam,
    createdAt: now,
    updatedAt: now,
    teams: teams,
    toss: toss,
    result: result,
    innings: innings,
    completedAt: completedAt,
    readinessIssues: readinessIssues,
  );
}

MatchTeam sampleMatchTeam({
  required String id,
  required String teamId,
  required MatchSide side,
  required String name,
  List<MatchPlayer> players = const [],
}) {
  return MatchTeam(
    id: id,
    teamId: teamId,
    side: side,
    name: name,
    shortName: name.length >= 2 ? name.substring(0, 2).toUpperCase() : name,
    players: players,
  );
}

class FakeMatchRepository implements MatchRepository {
  FakeMatchRepository({
    List<MatchDetail>? matches,
    Map<String, Team>? teams,
    Map<String, List<RosterMember>>? roster,
  }) : details = {
         for (final match in matches ?? const <MatchDetail>[]) match.id: match,
       },
       teams = Map.of(teams ?? const {}),
       rosterByTeam = {
         for (final entry in (roster ?? const {}).entries)
           entry.key: List.of(entry.value),
       };

  final Map<String, MatchDetail> details;
  final Map<String, Team> teams;
  final Map<String, List<RosterMember>> rosterByTeam;
  int _seq = 0;
  int listCalls = 0;
  Duration? listDelay;
  ApiException? createError;
  ApiException? readyError;
  ApiException? listError;
  ApiException? listMoreError;

  List<MatchSummary> get summaries =>
      details.values.map((match) => match.toSummary()).toList()
        ..sort((a, b) => b.createdAt.compareTo(a.createdAt));

  @override
  Future<MatchListPage> listMatches({
    MatchStatus? status,
    MatchListScope? scope,
    MatchFormat? format,
    String? teamId,
    String? search,
    DateTime? dateFrom,
    DateTime? dateTo,
    int limit = 20,
    int offset = 0,
  }) async {
    listCalls += 1;
    if (listDelay != null) {
      await Future<void>.delayed(listDelay!);
    }
    if (offset > 0 && listMoreError != null) {
      throw listMoreError!;
    }
    if (listError != null) {
      throw listError!;
    }
    var items = summaries;
    if (status != null) {
      items = items.where((match) => match.status == status).toList();
    } else if (scope == MatchListScope.active) {
      items = items
          .where((match) => MatchStatus.activeStatuses.contains(match.status))
          .toList();
    } else if (scope == MatchListScope.history) {
      items = items
          .where((match) => match.status == MatchStatus.completed)
          .toList();
    }
    if (format != null) {
      items = items.where((match) => match.format == format).toList();
    }
    if (teamId != null) {
      items = items.where((match) {
        final detail = details[match.id];
        return detail?.teams.any((team) => team.teamId == teamId) ?? false;
      }).toList();
    }
    final term = search?.trim().toLowerCase() ?? '';
    if (term.isNotEmpty) {
      items = items.where((match) {
        final haystack = [
          match.name,
          match.venueName,
          match.teamAName,
          match.teamBName,
        ].whereType<String>().join(' ').toLowerCase();
        return haystack.contains(term);
      }).toList();
    }
    final historyDates =
        scope == MatchListScope.history || status == MatchStatus.completed;
    if (dateFrom != null || dateTo != null) {
      items = items.where((match) {
        final stamp = historyDates
            ? match.completedAt ?? match.createdAt
            : match.createdAt;
        if (dateFrom != null && stamp.isBefore(dateFrom)) {
          return false;
        }
        if (dateTo != null && stamp.isAfter(dateTo)) {
          return false;
        }
        return true;
      }).toList();
    }
    if (scope == MatchListScope.history || status == MatchStatus.completed) {
      items.sort((a, b) {
        final aTime = a.completedAt ?? a.createdAt;
        final bTime = b.completedAt ?? b.createdAt;
        final compared = bTime.compareTo(aTime);
        return compared != 0 ? compared : b.id.compareTo(a.id);
      });
    } else if (scope == MatchListScope.active) {
      int rank(MatchStatus value) => switch (value) {
        MatchStatus.live => 0,
        MatchStatus.ready => 1,
        _ => 2,
      };
      items.sort((a, b) {
        final compared = rank(a.status).compareTo(rank(b.status));
        return compared != 0 ? compared : b.updatedAt.compareTo(a.updatedAt);
      });
    }
    final total = items.length;
    final page = items.skip(offset).take(limit).toList();
    return MatchListPage(
      items: page,
      total: total,
      limit: limit,
      offset: offset,
    );
  }

  @override
  Future<MatchDetail> getMatch(String id) async {
    final match = details[id];
    if (match == null) {
      throw const ApiException(
        'Match not found.',
        statusCode: 404,
        code: 'MATCH_NOT_FOUND',
      );
    }
    return match.copyWith(readinessIssues: _issues(match));
  }

  @override
  Future<MatchDetail> createDraft({
    required MatchFormat format,
    String? name,
    int? oversPerInnings,
    int ballsPerOver = 6,
    String? venueName,
    DateTime? scheduledAt,
    int playersPerTeam = 11,
  }) async {
    if (createError != null) {
      throw createError!;
    }
    if (format == MatchFormat.test) {
      throw const ApiException(
        'This match format is not supported.',
        statusCode: 400,
        code: 'INVALID_MATCH_FORMAT',
      );
    }
    final overs = format.locksOvers
        ? format.defaultOvers
        : (oversPerInnings ?? format.defaultOvers);
    if (overs < 1 || overs > 50) {
      throw const ApiException(
        'Overs per innings must be between 1 and 50.',
        statusCode: 400,
        code: 'INVALID_OVERS',
      );
    }
    _seq += 1;
    final now = DateTime.now().toUtc();
    final match = MatchDetail(
      id: 'match-$_seq',
      name: name,
      format: format,
      status: MatchStatus.draft,
      venueName: venueName,
      scheduledAt: scheduledAt,
      oversPerInnings: overs,
      ballsPerOver: ballsPerOver,
      playersPerTeam: playersPerTeam,
      createdAt: now,
      updatedAt: now,
    );
    details[match.id] = match;
    return match;
  }

  @override
  Future<MatchDetail> updateMatch(
    String id, {
    String? name,
    bool clearName = false,
    MatchFormat? format,
    int? oversPerInnings,
    int? ballsPerOver,
    String? venueName,
    bool clearVenue = false,
    DateTime? scheduledAt,
    bool clearScheduledAt = false,
    int? playersPerTeam,
  }) async {
    final current = await getMatch(id);
    _assertEditable(current);
    var nextFormat = format ?? current.format;
    var nextOvers = oversPerInnings ?? current.oversPerInnings;
    if (format != null && format.locksOvers) {
      nextOvers = format.defaultOvers;
    }
    if (nextOvers < 1 || nextOvers > 50) {
      throw const ApiException(
        'Overs per innings must be between 1 and 50.',
        statusCode: 400,
        code: 'INVALID_OVERS',
      );
    }
    final updated = current.copyWith(
      name: clearName ? null : (name ?? current.name),
      format: nextFormat,
      oversPerInnings: nextOvers,
      ballsPerOver: ballsPerOver,
      venueName: clearVenue ? null : (venueName ?? current.venueName),
      scheduledAt: scheduledAt,
      clearScheduledAt: clearScheduledAt,
      playersPerTeam: playersPerTeam,
      status: current.status == MatchStatus.ready
          ? MatchStatus.draft
          : current.status,
    );
    details[id] = updated;
    return updated;
  }

  @override
  Future<MatchDetail> setTeams(
    String id, {
    required String teamAId,
    required String teamBId,
  }) async {
    final current = await getMatch(id);
    _assertEditable(current);
    if (teamAId == teamBId) {
      throw const ApiException(
        'Choose two different teams.',
        statusCode: 409,
        code: 'SAME_TEAM_SELECTED',
      );
    }
    final teamA = _requireTeam(teamAId);
    final teamB = _requireTeam(teamBId);
    final previousA = current.teamA;
    final previousB = current.teamB;
    final nextA = sampleMatchTeam(
      id: previousA?.teamId == teamAId ? previousA!.id : 'mt-a-$id',
      teamId: teamA.id,
      side: MatchSide.teamA,
      name: teamA.name,
      players: previousA?.teamId == teamAId ? previousA!.players : const [],
    );
    final nextB = sampleMatchTeam(
      id: previousB?.teamId == teamBId ? previousB!.id : 'mt-b-$id',
      teamId: teamB.id,
      side: MatchSide.teamB,
      name: teamB.name,
      players: previousB?.teamId == teamBId ? previousB!.players : const [],
    );
    final updated = current.copyWith(
      teams: [nextA, nextB],
      clearToss: true,
      status: MatchStatus.draft,
    );
    details[id] = updated;
    return updated;
  }

  @override
  Future<MatchDetail> setPlayingXi(
    String id, {
    required List<PlayingXiTeamInput> teams,
  }) async {
    final current = await getMatch(id);
    _assertEditable(current);
    var nextTeams = [...current.teams];
    final seen = <String>{};
    for (final payload in teams) {
      final index = nextTeams.indexWhere(
        (team) => team.id == payload.matchTeamId,
      );
      if (index < 0) {
        throw const ApiException(
          'Match not found.',
          statusCode: 404,
          code: 'MATCH_NOT_FOUND',
        );
      }
      final matchTeam = nextTeams[index];
      final roster = rosterByTeam[matchTeam.teamId] ?? const <RosterMember>[];
      final players = <MatchPlayer>[];
      for (final item in payload.players) {
        if (seen.contains(item.playerId)) {
          throw const ApiException(
            'A player can only appear once in a match.',
            statusCode: 409,
            code: 'DUPLICATE_PLAYING_XI_PLAYER',
          );
        }
        seen.add(item.playerId);
        final member = roster
            .where((row) => row.playerId == item.playerId)
            .firstOrNull;
        if (member == null || !member.isActive) {
          throw const ApiException(
            'That player is not on this team\'s active roster.',
            statusCode: 409,
            code: 'PLAYER_NOT_IN_ROSTER',
          );
        }
        players.add(
          MatchPlayer(
            id: 'mp-${member.playerId}',
            playerId: member.playerId,
            name: member.name,
            isPlaying: true,
            isCaptain: item.isCaptain,
            isWicketKeeper: item.isWicketKeeper,
            battingPosition: item.battingPosition,
            role: member.role,
          ),
        );
      }
      nextTeams[index] = matchTeam.copyWith(players: players);
    }
    final updated = current.copyWith(
      teams: nextTeams,
      status: MatchStatus.draft,
    );
    details[id] = updated;
    return updated;
  }

  @override
  Future<MatchDetail> setToss(
    String id, {
    required String winnerMatchTeamId,
    required TossDecision decision,
  }) async {
    final current = await getMatch(id);
    _assertEditable(current);
    final belongs = current.teams.any((team) => team.id == winnerMatchTeamId);
    if (!belongs) {
      throw const ApiException(
        'Toss winner must be one of the match teams.',
        statusCode: 409,
        code: 'TOSS_TEAM_INVALID',
      );
    }
    final updated = current.copyWith(
      toss: MatchToss(winnerMatchTeamId: winnerMatchTeamId, decision: decision),
      status: MatchStatus.draft,
    );
    details[id] = updated;
    return updated;
  }

  @override
  Future<MatchDetail> markReady(String id) async {
    if (readyError != null) {
      throw readyError!;
    }
    final current = await getMatch(id);
    _assertEditable(current);
    final issues = _issues(current);
    if (issues.isNotEmpty) {
      throw ApiException(
        'Match configuration is incomplete.',
        statusCode: 409,
        code: 'MATCH_NOT_READY',
        details: issues,
      );
    }
    final updated = current.copyWith(
      status: MatchStatus.ready,
      readinessIssues: const [],
    );
    details[id] = updated;
    return updated;
  }

  Team _requireTeam(String id) {
    final team = teams[id];
    if (team == null) {
      throw const ApiException(
        'Team not found.',
        statusCode: 404,
        code: 'TEAM_NOT_FOUND',
      );
    }
    if (!team.isActive) {
      throw const ApiException(
        'This team is currently inactive.',
        statusCode: 409,
        code: 'INACTIVE_TEAM',
      );
    }
    return team;
  }

  void _assertEditable(MatchDetail match) {
    if (!match.status.isEditable) {
      throw const ApiException(
        'This match can no longer be configured.',
        statusCode: 409,
        code: 'MATCH_NOT_EDITABLE',
      );
    }
  }

  List<String> _issues(MatchDetail match) {
    final issues = <String>[];
    if (match.teamA == null || match.teamB == null) {
      issues.add('Select two teams.');
    }
    void xi(String label, MatchTeam? team) {
      if (team == null) {
        return;
      }
      if (team.players.length != match.playersPerTeam) {
        issues.add(
          '$label Playing XI requires ${match.playersPerTeam} players.',
        );
      }
      if (team.captain == null) {
        issues.add('$label captain is not selected.');
      }
      if (team.keeper == null) {
        issues.add('$label wicketkeeper is not selected.');
      }
    }

    xi('Team A', match.teamA);
    xi('Team B', match.teamB);
    if (match.toss == null) {
      issues.add('Set the toss winner and decision.');
    }
    return issues;
  }
}
