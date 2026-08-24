import 'package:ai_cric_scoring/core/cricket/player_attributes.dart';
import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/players/data/models/player.dart';
import 'package:ai_cric_scoring/features/players/data/repositories/player_repository.dart';
import 'package:ai_cric_scoring/features/teams/data/models/roster_member.dart';
import 'package:ai_cric_scoring/features/teams/data/models/team.dart';
import 'package:ai_cric_scoring/features/teams/data/repositories/team_repository.dart';

Team sampleTeam({
  String id = 'team-1',
  String name = 'Weekend Warriors',
  String? shortName = 'WW',
  int playerCount = 0,
  bool isActive = true,
}) {
  return Team(
    id: id,
    name: name,
    shortName: shortName,
    isActive: isActive,
    playerCount: playerCount,
  );
}

Player samplePlayer({
  String id = 'player-1',
  String name = 'Rahul Shah',
  PlayerRole role = PlayerRole.batter,
  BattingStyle battingStyle = BattingStyle.rightHanded,
  BowlingStyle bowlingStyle = BowlingStyle.unknown,
  bool isActive = true,
  List<TeamSummary> teams = const [],
}) {
  return Player(
    id: id,
    name: name,
    role: role,
    battingStyle: battingStyle,
    bowlingStyle: bowlingStyle,
    isActive: isActive,
    teams: teams,
  );
}

RosterMember sampleRosterMember({
  String membershipId = 'membership-1',
  String playerId = 'player-1',
  String name = 'Rahul Shah',
  PlayerRole role = PlayerRole.batter,
  BattingStyle battingStyle = BattingStyle.rightHanded,
  bool isActive = true,
}) {
  return RosterMember(
    membershipId: membershipId,
    playerId: playerId,
    name: name,
    role: role,
    battingStyle: battingStyle,
    bowlingStyle: BowlingStyle.unknown,
    isActive: isActive,
  );
}

class FakeTeamRepository implements TeamRepository {
  FakeTeamRepository({
    List<Team>? teams,
    Map<String, List<RosterMember>>? roster,
    List<Player>? playerPool,
  }) : teams = List.of(teams ?? const []),
       playerPool = List.of(playerPool ?? const []),
       rosterByTeam = {
         for (final entry in (roster ?? const {}).entries)
           entry.key: List.of(entry.value),
       };

  final List<Team> teams;
  final List<Player> playerPool;
  final Map<String, List<RosterMember>> rosterByTeam;
  ApiException? createError;
  ApiException? addError;

  @override
  Future<List<Team>> listTeams({String? search, bool? isActive}) async {
    var items = List<Team>.from(teams);
    if (search != null && search.isNotEmpty) {
      final needle = search.toLowerCase();
      items = items
          .where(
            (team) =>
                team.name.toLowerCase().contains(needle) ||
                (team.shortName?.toLowerCase().contains(needle) ?? false),
          )
          .toList();
    }
    if (isActive != null) {
      items = items.where((team) => team.isActive == isActive).toList();
    }
    return items;
  }

  @override
  Future<Team> getTeam(String id) async {
    return teams.firstWhere(
      (team) => team.id == id,
      orElse: () => throw const ApiException(
        'Team not found.',
        statusCode: 404,
        code: 'TEAM_NOT_FOUND',
      ),
    );
  }

  @override
  Future<Team> createTeam({required String name, String? shortName}) async {
    if (createError != null) {
      throw createError!;
    }
    if (teams.any((team) => team.name.toLowerCase() == name.toLowerCase())) {
      throw const ApiException(
        'You already have a team with this name.',
        statusCode: 409,
        code: 'TEAM_NAME_ALREADY_EXISTS',
      );
    }
    final team = Team(
      id: 'team-${teams.length + 1}',
      name: name,
      shortName: shortName,
      isActive: true,
      playerCount: 0,
    );
    teams.add(team);
    return team;
  }

  @override
  Future<Team> updateTeam(
    String id, {
    String? name,
    String? shortName,
    bool clearShortName = false,
    bool? isActive,
  }) async {
    final index = teams.indexWhere((team) => team.id == id);
    if (index < 0) {
      throw const ApiException(
        'Team not found.',
        statusCode: 404,
        code: 'TEAM_NOT_FOUND',
      );
    }
    var team = teams[index];
    if (name != null &&
        teams.any(
          (other) =>
              other.id != id && other.name.toLowerCase() == name.toLowerCase(),
        )) {
      throw const ApiException(
        'You already have a team with this name.',
        statusCode: 409,
        code: 'TEAM_NAME_ALREADY_EXISTS',
      );
    }
    team = team.copyWith(
      name: name,
      shortName: clearShortName ? null : shortName,
      isActive: isActive,
    );
    if (clearShortName) {
      team = Team(
        id: team.id,
        name: team.name,
        isActive: team.isActive,
        playerCount: team.playerCount,
      );
    }
    teams[index] = team;
    return team;
  }

  @override
  Future<List<RosterMember>> listRoster(
    String teamId, {
    bool includeInactive = false,
  }) async {
    await getTeam(teamId);
    final items = List<RosterMember>.from(rosterByTeam[teamId] ?? const []);
    if (includeInactive) {
      return items;
    }
    return items.where((member) => member.isActive).toList();
  }

  @override
  Future<RosterMember> addPlayer(String teamId, String playerId) async {
    if (addError != null) {
      throw addError!;
    }
    final team = await getTeam(teamId);
    final current = rosterByTeam.putIfAbsent(teamId, () => []);
    final existingIndex = current.indexWhere(
      (member) => member.playerId == playerId,
    );
    if (existingIndex >= 0) {
      final existing = current[existingIndex];
      if (existing.isActive) {
        throw const ApiException(
          'This player is already in the roster.',
          statusCode: 409,
          code: 'PLAYER_ALREADY_IN_TEAM',
        );
      }
      final reactivated = RosterMember(
        membershipId: existing.membershipId,
        playerId: existing.playerId,
        name: existing.name,
        role: existing.role,
        battingStyle: existing.battingStyle,
        bowlingStyle: existing.bowlingStyle,
        isActive: true,
      );
      current[existingIndex] = reactivated;
      _setCount(teamId, team.playerCount + 1);
      return reactivated;
    }
    Player? player;
    for (final item in playerPool) {
      if (item.id == playerId) {
        player = item;
        break;
      }
    }
    if (player == null) {
      throw const ApiException(
        'Player not found.',
        statusCode: 404,
        code: 'PLAYER_NOT_FOUND',
      );
    }
    final member = RosterMember(
      membershipId: 'membership-${current.length + 1}',
      playerId: player.id,
      name: player.name,
      role: player.role,
      battingStyle: player.battingStyle,
      bowlingStyle: player.bowlingStyle,
      isActive: true,
    );
    current.add(member);
    _setCount(teamId, team.playerCount + 1);
    return member;
  }

  void _setCount(String teamId, int count) {
    final index = teams.indexWhere((team) => team.id == teamId);
    if (index >= 0) {
      teams[index] = teams[index].copyWith(playerCount: count);
    }
  }

  @override
  Future<void> removePlayer(String teamId, String playerId) async {
    final team = await getTeam(teamId);
    final current = rosterByTeam[teamId] ?? [];
    final index = current.indexWhere((member) => member.playerId == playerId);
    if (index < 0) {
      throw const ApiException(
        'This player is not on the team roster.',
        statusCode: 404,
        code: 'PLAYER_NOT_IN_TEAM',
      );
    }
    final existing = current[index];
    if (!existing.isActive) {
      throw const ApiException(
        'This player is not on the team roster.',
        statusCode: 404,
        code: 'PLAYER_NOT_IN_TEAM',
      );
    }
    current[index] = RosterMember(
      membershipId: existing.membershipId,
      playerId: existing.playerId,
      name: existing.name,
      role: existing.role,
      battingStyle: existing.battingStyle,
      bowlingStyle: existing.bowlingStyle,
      isActive: false,
    );
    _setCount(teamId, team.playerCount - 1);
  }
}

class FakePlayerRepository implements PlayerRepository {
  FakePlayerRepository({List<Player>? players})
    : players = List.of(players ?? const []);

  final List<Player> players;
  ApiException? createError;

  @override
  Future<List<Player>> listPlayers({
    String? search,
    PlayerRole? role,
    bool? isActive,
  }) async {
    var items = List<Player>.from(players);
    if (search != null && search.isNotEmpty) {
      final needle = search.toLowerCase();
      items = items
          .where((player) => player.name.toLowerCase().contains(needle))
          .toList();
    }
    if (role != null) {
      items = items.where((player) => player.role == role).toList();
    }
    if (isActive != null) {
      items = items.where((player) => player.isActive == isActive).toList();
    }
    return items;
  }

  @override
  Future<Player> getPlayer(String id) async {
    return players.firstWhere(
      (player) => player.id == id,
      orElse: () => throw const ApiException(
        'Player not found.',
        statusCode: 404,
        code: 'PLAYER_NOT_FOUND',
      ),
    );
  }

  @override
  Future<Player> createPlayer({
    required String name,
    required PlayerRole role,
    required BattingStyle battingStyle,
    required BowlingStyle bowlingStyle,
  }) async {
    if (createError != null) {
      throw createError!;
    }
    final player = Player(
      id: 'player-${players.length + 1}',
      name: name,
      role: role,
      battingStyle: battingStyle,
      bowlingStyle: bowlingStyle,
      isActive: true,
    );
    players.add(player);
    return player;
  }

  @override
  Future<Player> updatePlayer(
    String id, {
    String? name,
    PlayerRole? role,
    BattingStyle? battingStyle,
    BowlingStyle? bowlingStyle,
    bool? isActive,
  }) async {
    final index = players.indexWhere((player) => player.id == id);
    if (index < 0) {
      throw const ApiException(
        'Player not found.',
        statusCode: 404,
        code: 'PLAYER_NOT_FOUND',
      );
    }
    final updated = players[index].copyWith(
      name: name,
      role: role,
      battingStyle: battingStyle,
      bowlingStyle: bowlingStyle,
      isActive: isActive,
    );
    players[index] = updated;
    return updated;
  }
}
