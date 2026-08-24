from app.rag import rerank as rerank_module
from app.rag import store as store_module
from app.rag.pipeline import ask
from app.rag.rerank import Reranker
from app.rag.store import Store

# expected_source = which file SHOULD be retrieved
# None = the system should refuse
TEST_SET = [
    # --- Answerable ---
    {"q": "How many days of paid sick leave do I get?",
     "expected_source": "leave_policy.md"},
    {"q": "What is the home office stipend amount?",
     "expected_source": "remote_work_policy.md"},
    {"q": "How much annual leave do I get?",
     "expected_source": "leave_policy.md"},
    {"q": "How often must I change my password?",
     "expected_source": "security_guidelines.md"},
    {"q": "What is the daily meal allowance when travelling?",
     "expected_source": "expense_reimbursement.md"},
    {"q": "How many days per week can I work from home?",
     "expected_source": "remote_work_policy.md"},
    {"q": "When must I report a stolen laptop?",
     "expected_source": "security_guidelines.md"},

    # --- Hard negatives (topically close, answer absent) ---
    {"q": "What is the meal allowance for international travel?",
     "expected_source": None},
    {"q": "Can I carry forward my sick leave days?",
     "expected_source": "leave_policy.md"},

    # --- Clearly out of scope ---
    {"q": "What is the company's policy on office pets?",
     "expected_source": None},
    {"q": "How do I file my income tax return?",
     "expected_source": None},
    {"q": "How frequently do I need to update my password?",
     "expected_source": "security_guidelines.md"},
    {"q": "What is the password rotation period?",
     "expected_source": "security_guidelines.md"},
    {"q": "Is there a rule about changing passwords regularly?",
     "expected_source": "security_guidelines.md"},
]


def init_models():
    store_module.store = Store()
    rerank_module.reranker = Reranker()


def run_eval():
    init_models()
    rows = []
    for case in TEST_SET:
        result = ask(case["q"])
        hits = result["sources"]

        sources = [h["source"] for h in hits]
        top_distance = hits[0]["distance"] if hits else None
        refused = result["refused"]

        if case["expected_source"] is None:
            correct = refused
        else:
            correct = (case["expected_source"] in sources) and not refused

        rows.append({
            "question": case["q"],
            "expected": case["expected_source"] or "REFUSE",
            "top_source": sources[0] if sources else "-",
            "distance": top_distance,
            "refused": refused,
            "correct": correct,
        })
    return rows


if __name__ == "__main__":
    rows = run_eval()

    print(f"{'Question':<52} {'Expected':<24} {'Got':<24} {'Dist':<8} {'OK'}")
    print("-" * 118)
    for r in rows:
        got = "REFUSED" if r["refused"] else r["top_source"]
        dist = f"{r['distance']:.3f}" if r["distance"] is not None else "-"
        mark = "PASS" if r["correct"] else "FAIL"
        print(f"{r['question'][:50]:<52} {r['expected']:<24} "
              f"{got:<24} {dist:<8} {mark}")

    passed = sum(1 for r in rows if r["correct"])
    print("-" * 118)
    print(f"Score: {passed}/{len(rows)} correct "
          f"({passed / len(rows) * 100:.0f}%)")
