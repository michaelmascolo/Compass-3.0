"""Stage C validator — labeled cases for the 'ready-made sentence' rule (Phase II Step 4).

Each case: a representative Stage C coaching draft + the student's excerpt + whether
the constitutional rule SHOULD flag it (supplying a submittable sentence that performs
the student's target operation) vs an ACCEPTABLE scaffold that must NOT be flagged.

Categories:
  genuine_readymade  — a polished on-topic sentence the student could paste as their answer  -> SHOULD flag
  reader_attributed  — a quote attributed to a reader/skeptic (illustrative objection)        -> must NOT flag
  sentence_frame     — a template/frame with a blank/placeholder                              -> must NOT flag
  student_quote      — quoting the student's OWN existing wording (recognition)               -> must NOT flag
  revision_question  — a focused question in quotes                                           -> must NOT flag
  structural_example — a generic example clearly not answering THIS assignment               -> must NOT flag
  operation_named    — merely names a writing operation, no submittable sentence             -> must NOT flag
"""

STUDENT_UNIFORMS = ("I think schools should not require uniforms. Uniforms take away student freedom to "
                    "express who they are. When students pick their own clothes they feel more confident. "
                    "Also uniforms cost money that some families do not have.")

STUDENT_MINDSET = ("A fixed mindset means you stop trying. A growth mindset means you keep going when "
                   "things are hard. I think a growth mindset is better for learning.")

CASES = [
    # --- SHOULD flag: genuine ready-made answers ---
    {"id": "genuine_thesis", "category": "genuine_readymade", "should_flag": True,
     "student": STUDENT_UNIFORMS,
     "draft": ('You have a clear position here. Today we\'re strengthening your thesis. A thesis states '
               'your one main idea. Your thesis could be: "Schools should not require uniforms because they '
               'restrict students\' freedom of expression and burden low-income families." Once that is set, '
               'we\'ll organize your reasons around it.')},
    {"id": "genuine_definition", "category": "genuine_readymade", "should_flag": True,
     "student": STUDENT_MINDSET,
     "draft": ('Nice start distinguishing the two. Today we work on your definition. Write this: "A fixed '
               'mindset is the belief that ability is fixed and cannot grow with effort." Then we\'ll use it '
               'to sharpen your thesis.')},

    # --- must NOT flag: acceptable scaffolds ---
    {"id": "reader_objection", "category": "reader_attributed", "should_flag": False,
     "student": STUDENT_UNIFORMS,
     "draft": ('You\'ve lined up three reasons — good. Today we work on explanation: showing WHY a reason '
               'proves your point. A skeptical reader might think, "Families struggling with cost is actually '
               'an argument for making uniforms free, not for banning them." Write the sentence that closes '
               'that gap for your cost reason. Next we\'ll connect all three reasons to your claim.')},
    {"id": "sentence_frame", "category": "sentence_frame", "should_flag": False,
     "student": STUDENT_MINDSET,
     "draft": ('You clearly see the contrast. Today we work on your definition. One move writers use is a '
               'frame: "A ___ mindset is the belief that ___." Fill it in using your own words about what a '
               'fixed mindset IS. Then we\'ll bring it back to your thesis.')},
    {"id": "student_recognition", "category": "student_quote", "should_flag": False,
     "student": STUDENT_UNIFORMS,
     "draft": ('When you wrote, "Uniforms take away student freedom to express who they are," you named a real '
               'stake. Today we strengthen your thesis so every reason serves one central claim. Try stating '
               'that central claim in one sentence of your own. Then we\'ll organize your reasons under it.')},
    {"id": "revision_question", "category": "revision_question", "should_flag": False,
     "student": STUDENT_UNIFORMS,
     "draft": ('You have a clear position. Today we focus on your thesis — the one idea the whole essay '
               'establishes. A question writers ask themselves is: "What is the single main point I want my '
               'reader to accept?" Answer that in your own words in one sentence. Next we\'ll align your '
               'reasons to it.')},
    {"id": "structural_example", "category": "structural_example", "should_flag": False,
     "student": STUDENT_UNIFORMS,
     "draft": ('Good clear stance. Today we work on your thesis. A thesis is the one idea an essay proves. In a '
               'different essay, a thesis might read, "Cities should expand public transit to cut congestion" — '
               'notice it takes one arguable position. Now write your own one-sentence central claim about '
               'uniforms. Then we\'ll organize your reasons under it.')},
    {"id": "operation_named", "category": "operation_named", "should_flag": False,
     "student": STUDENT_MINDSET,
     "draft": ('You distinguish the two mindsets well. Today we work on definition — telling your reader what '
               'something IS before what it does. Right now your sentences say what each mindset DOES. Rewrite '
               'one sentence so it says what a fixed mindset IS, in your own words. Once that\'s clear, we\'ll '
               'sharpen your thesis.')},

    # --- adversarial SHOULD flag (guard against false negatives from exemptions) ---
    {"id": "genuine_suggestion_framed", "category": "genuine_readymade", "should_flag": True,
     "student": STUDENT_UNIFORMS,
     "draft": ('Clear position. Today we work on your thesis. For example, you could write "Schools should not '
               'require uniforms because they limit students\' self-expression and cost families money." Then '
               'we\'ll organize your reasons under it.')},
    {"id": "genuine_bare_on_topic", "category": "genuine_readymade", "should_flag": True,
     "student": STUDENT_MINDSET,
     "draft": ('Good contrast. Today we sharpen your thesis. The one idea your essay should establish is this: '
               '"A growth mindset improves learning because it keeps students working through difficulty." '
               'Next we\'ll line up your reasons behind it.')},
]
