import 'package:ai_cric_scoring/core/errors/api_exception.dart';
import 'package:ai_cric_scoring/features/ai_chat/data/models/match_chat.dart';
import 'package:ai_cric_scoring/features/ai_chat/data/repositories/match_chat_repository.dart';

MatchChatMessage sampleUserMessage({
  String id = 'user-1',
  String content = 'Who won the match?',
  String clientMessageId = 'client-1',
}) {
  return MatchChatMessage(
    id: id,
    role: 'USER',
    content: content,
    createdAt: DateTime.utc(2026, 8, 16, 9, 40),
    clientMessageId: clientMessageId,
  );
}

MatchChatMessage sampleAssistantMessage({
  String id = 'ai-1',
  String content = 'Weekend Warriors won by 12 runs.',
  ChatAnswerType answerType = ChatAnswerType.directStat,
  List<ChatEvidence> evidence = const [],
  List<ChatClarificationOption> options = const [],
  List<String> suggestions = const ['Who was the top scorer?'],
}) {
  return MatchChatMessage(
    id: id,
    role: 'ASSISTANT',
    content: content,
    createdAt: DateTime.utc(2026, 8, 16, 9, 41),
    answerType: answerType,
    evidence: evidence,
    clarificationOptions: options,
    followUpSuggestions: suggestions,
  );
}

class FakeMatchChatRepository implements MatchChatRepository {
  FakeMatchChatRepository({
    List<MatchChatMessage>? messages,
    this.sendError,
    this.generationError,
    this.sendDelay = Duration.zero,
  }) : messages = List.of(messages ?? const []);

  final List<MatchChatMessage> messages;
  Object? sendError;
  ChatGenerationError? generationError;
  Duration sendDelay;
  int sendCalls = 0;
  String? lastMessage;

  @override
  Future<ChatHistoryPage> getMessages(
    String matchId, {
    String? beforeId,
    int limit = 30,
  }) async {
    return ChatHistoryPage(messages: List.of(messages), hasMore: false);
  }

  @override
  Future<SendChatResult> sendMessage({
    required String matchId,
    required String message,
    required String clientMessageId,
  }) async {
    sendCalls += 1;
    lastMessage = message;
    if (sendDelay > Duration.zero) {
      await Future<void>.delayed(sendDelay);
    }
    if (sendError != null) {
      throw sendError!;
    }
    final user = sampleUserMessage(
      id: 'user-$clientMessageId',
      content: message,
      clientMessageId: clientMessageId,
    );
    messages.add(user);
    if (generationError != null) {
      return SendChatResult(
        userMessage: user,
        generationError: generationError,
      );
    }
    final assistant = _reply(message);
    messages.add(assistant);
    return SendChatResult(userMessage: user, assistantMessage: assistant);
  }

  MatchChatMessage _reply(String message) {
    final lowered = message.toLowerCase();
    if (lowered.contains('rahul') &&
        !lowered.contains('shah') &&
        !lowered.contains('patel')) {
      return sampleAssistantMessage(
        content: 'Which Rahul do you mean — Rahul Shah or Rahul Patel?',
        answerType: ChatAnswerType.clarification,
        options: const [
          ChatClarificationOption(
            label: 'Rahul Shah',
            message: 'I mean Rahul Shah.',
          ),
          ChatClarificationOption(
            label: 'Rahul Patel',
            message: 'I mean Rahul Patel.',
          ),
        ],
        suggestions: const [],
      );
    }
    if (lowered.contains('why')) {
      return sampleAssistantMessage(
        content:
            'Warriors lost mainly because three wickets fell in the middle overs.',
        answerType: ChatAnswerType.analytical,
        evidence: const [
          ChatEvidence(
            factId: 'fow_2_3',
            type: 'fall_of_wicket',
            label: 'Wicket cluster',
            summary: '3 wickets fell between overs 12.2 and 14.1',
          ),
        ],
      );
    }
    if (lowered.contains('weather') || lowered.contains('pitch')) {
      return sampleAssistantMessage(
        content:
            'Pitch conditions were not recorded for this match, so I cannot determine that from the match data.',
        suggestions: const [],
      );
    }
    if (lowered.contains('ipl') || lowered.contains('world')) {
      return sampleAssistantMessage(
        content:
            'I can answer questions about this match. Ask me about the score, players, partnerships, bowling, turning points, or result.',
        answerType: ChatAnswerType.outOfScope,
        suggestions: const [],
      );
    }
    return sampleAssistantMessage();
  }
}

ApiException chatUnavailable() {
  return const ApiException(
    'Unable to generate analysis right now.',
    code: 'AI_TIMEOUT',
    statusCode: 504,
  );
}
