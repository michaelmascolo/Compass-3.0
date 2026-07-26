"""Generate precomputed Teacher Review fixtures by running the REAL frozen engine
on the six approved sample cases. No engine changes — uses the normal API path so
the full DevelopmentalTheory is produced (not the preview-trimmed output)."""
import asyncio, json, httpx

BASE = "http://localhost:8001/api"

ASSIGNMENT = ("Some schools have banned personal cell phones during class. Write one paragraph "
              "arguing whether your school should allow or ban personal cell phones during class. "
              "Take a clear position and support it with reasons and examples.")
PURPOSE = ("Help the student clarify and develop their position so a reader understands and is "
           "persuaded, and understand what each part of the writing is doing for the reader.")
TASK = "Write one paragraph arguing your position, with reasons and examples."
NOTES = "The writer is a high school student. Respond developmentally to their actual paragraph."

CASES = [
    ("student-a", "Student A", "I think phones should be allowed because they help people. Sometimes students need them if something happens at home, and they can also help us look things up. It isn't fair that everyone loses their phones because a few students don't pay attention."),
    ("student-b", "Student B", "I believe our school should allow personal cell phones during class. Phones can actually help students learn because we can look up information quickly and use apps for studying. Some teachers even use phones for classroom activities like polls. As long as students use them responsibly, phones can be a useful tool instead of a distraction."),
    ("student-c", "Student C", "While many worry that cell phones distract students, our school should allow them during class under clear guidelines. Phones are powerful learning tools: students can access research, translate unfamiliar terms, and organize assignments in seconds. A complete ban assumes students cannot learn self-control, yet responsible use is itself a skill worth teaching. Rather than removing phones entirely, teachers could set 'phone-on' and 'phone-off' times, helping students practice the judgment they will need long after high school."),
    ("student-d", "Student D", "My favorite thing about school is lunchtime because I get to see my friends and we talk about weekend plans. The cafeteria food isn't always great, but sometimes they have pizza which everyone likes. I also enjoy gym class because we get to play basketball. School would be better if we had longer breaks between classes."),
    ("student-e", "Student E", "Personal cell phones should be allowed during class when they are used for educational purposes and within clearly defined expectations. They provide students with immediate access to information, digital learning resources, and organizational tools that can enhance classroom learning. In addition, learning to use technology responsibly is an important skill that students will need beyond school. Although phones can become distracting if misused, thoughtful classroom guidelines can minimize these concerns while preserving the educational benefits. Overall, allowing responsible phone use creates opportunities for both academic growth and personal responsibility."),
    ("student-f", "Student F", "In my opinion the school need to allow the phone in class. Many student use phone for translate the difficult word, this help us to understand the lesson better. Also when we don't understand, we can search fast the information. If the school ban all phone, is more hard for student like me who still learning English. So I think phone can help if we use with respect."),
]


async def run_case(client, cid, label, response):
    s = (await client.post(f"{BASE}/sessions", json={
        "assignment": ASSIGNMENT, "pedagogical_purpose": PURPOSE,
        "current_writing_task": TASK, "teacher_notes": NOTES})).json()
    sid = s["id"]
    await client.post(f"{BASE}/sessions/{sid}/interact", json={"kind": "writing", "content": response})
    # poll until the AI turn completes
    for _ in range(120):
        await asyncio.sleep(2)
        sess = (await client.get(f"{BASE}/sessions/{sid}")).json()
        ai = [t for t in sess.get("turns", []) if t.get("role") == "ai"]
        if ai and ai[-1].get("status") == "complete":
            print(f"[done] {label} ({cid})")
            return {"id": cid, "label": label, "assignment": ASSIGNMENT, "response": response, "session": sess}
        if ai and ai[-1].get("status") == "failed":
            print(f"[FAILED] {label}")
            return {"id": cid, "label": label, "assignment": ASSIGNMENT, "response": response, "session": sess, "error": "failed"}
    print(f"[timeout] {label}")
    return {"id": cid, "label": label, "assignment": ASSIGNMENT, "response": response, "error": "timeout"}


async def main():
    async with httpx.AsyncClient(timeout=300) as client:
        results = await asyncio.gather(*[run_case(client, *c) for c in CASES])
    with open("/app/backend/teacher_review_fixtures.json", "w") as f:
        json.dump({"cases": results}, f, indent=2)
    print("WROTE /app/backend/teacher_review_fixtures.json")


if __name__ == "__main__":
    asyncio.run(main())
