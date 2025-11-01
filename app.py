import streamlit as st
import datetime
import pandas as pd

def force_scroll_top():
    st.components.v1.html(
        """
        <script>
        window.addEventListener('load', () => {
            setTimeout(() => {
                window.parent.document.documentElement.scrollTo(0, 0);
                window.parent.scrollTo(0, 0);
            }, 150);
        });
        </script>
        """,
        height=0,
    )

# ---------------------------
# INIT STATE
# ---------------------------

# Navigation step
if "step" not in st.session_state:
    st.session_state.step = 1

# Mars selection
if "mars" not in st.session_state:
    st.session_state.mars = None

# Time range defaults (datetime.time objects!)
if "time1" not in st.session_state:
    st.session_state.time1 = datetime.time(0, 0)

if "time2" not in st.session_state:
    st.session_state.time2 = datetime.time(23, 59)

# Hour lord timeline
if "hour_slots" not in st.session_state:
    st.session_state.hour_slots = []

# Last endpoint storage
if "final_end" not in st.session_state:
    st.session_state.final_end = None


# Zodiac & House cycles
zodiac_cycle = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces",
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

house_cycle = [
    "1","12","11","10","9","8","7","6","5","4","3","2",
    "1","12","11","10","9","8","7","6","5","4","3","2"
]


def expand_range(start, end, cycle):
    start_idx = cycle.index(start)
    end_idx = start_idx + cycle[start_idx:].index(end)
    return cycle[start_idx:end_idx+1]


# ---------------------------
# Time dropdown (HH & MM)
# ---------------------------
def time_selector(label, default=None):
    # Default time handling
    if isinstance(default, datetime.time):
        default_h = default.hour
        default_m = default.minute
    elif isinstance(default, str) and ":" in default:
        default_h = int(default.split(":")[0])
        default_m = int(default.split(":")[1])
    else:
        # first time load → default full day range
        default_h = 0 if "Time1" in label else 23
        default_m = 0 if "Time1" in label else 59

    col1, col2 = st.columns(2)
    with col1:
        h = st.selectbox(f"{label} Hour", list(range(24)), index=default_h)
    with col2:
        m = st.selectbox(f"{label} Min", list(range(60)), index=default_m)

    return datetime.time(hour=h, minute=m)


# ---------------------------
# STEP 1 — Mars selection
# ---------------------------
if st.session_state.step == 1:
    st.title("Birth Time Finder")

    mars = st.selectbox("Select your Mars sign", [
        "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
        "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
    ])

    if st.button("Next"):
        st.session_state.mars = mars
        st.session_state.step = 2
        st.rerun()

# ---------------------------
# STEP 2 — Select Time Range & baseline data
# ---------------------------
elif st.session_state.step == 2:
    st.header("Select Birth Time Range")
    st.write("Pick Time1 and Time2 (birth window)")

    # ---------------------------
    # TIME INPUT BLOCK
    # ---------------------------
    colA, colB = st.columns(2)

    with colA:
        time1 = time_selector("Time1", st.session_state.time1)
    with colB:
        time2 = time_selector("Time2", st.session_state.time2)

    # Keep stored times updated
    st.session_state.time1 = time1
    st.session_state.time2 = time2

    st.write("Enter astro info for Time1 & Time2 (start and end points)")

    # ---------------------------
    # T1 / T2 ASTRO FIELDS
    # ---------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Time1")
        t1_hl = st.selectbox("Hour Lord", ["Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"], key="t1_hl")
        t1_asc = st.selectbox("Ascendant", zodiac_cycle[:12], key="t1_asc")
        t1_sat = st.selectbox("Saturn House", [str(i) for i in range(1,13)], key="t1_sat")
        t1_chi = st.selectbox("Chiron House", [str(i) for i in range(1,13)], key="t1_chi")

    with col2:
        st.subheader("Time2")
        # Time2 has NO hour lord field by your design
        t2_asc = st.selectbox("Ascendant", zodiac_cycle[:12], key="t2_asc")
        t2_sat = st.selectbox("Saturn House", [str(i) for i in range(1,13)], key="t2_sat")
        t2_chi = st.selectbox("Chiron House", [str(i) for i in range(1,13)], key="t2_chi")

    # ---------------------------
    # SUBMIT
    # ---------------------------
    if st.button("Confirm Range & Proceed"):

        # store final end values for last expansion step
        st.session_state.final_end = {
            "asc": t2_asc,
            "sat": t2_sat,
            "chi": t2_chi
        }

        # first HL slot: ONLY store start point
        st.session_state.hour_slots.append({
            "hl": t1_hl,
            "start_time": time1,

            "asc_start": t1_asc,
            "sat_start": t1_sat,
            "chi_start": t1_chi,

            "asc_range": [t1_asc],
            "sat_range": [t1_sat],
            "chi_range": [t1_chi],

            "alive": True
        })

        st.session_state.step = 3
        st.rerun()

# ---------------------------
# STEP 3 — Hour Lord input loop
# ---------------------------
elif st.session_state.step == 3:
    st.header("Enter Hour Lord Sequence")

    t1 = st.session_state.time1.strftime("%H:%M")
    t2 = st.session_state.time2.strftime("%H:%M")
    st.write(f"Birth window: **{t1} → {t2}**")

    # Display timeline
    if st.session_state.hour_slots:
        st.subheader("Current Hour Lord Entries")

        t2 = st.session_state.time2.strftime("%H:%M")
        total = len(st.session_state.hour_slots)

        for i, slot in enumerate(st.session_state.hour_slots):

            # ✅ Display logic
            if "end_time" in slot and slot["end_time"] not in [None, "??:??"]:
                end_display = slot["end_time"]
            elif i == total - 1:  # last slot
                end_display = t2  # ✅ show birth-window end
            else:
                end_display = "??:??"

            st.write(
                f"**{i+1}.** {slot['start_time'].strftime('%H:%M')} → {end_display} — "
                f"{slot['hl']} | ASC {', '.join(slot['asc_range'])} | "
                f"SAT {', '.join(slot['sat_range'])} | CHI {', '.join(slot['chi_range'])}"
            )

        # Undo button
        if len(st.session_state.hour_slots) > 1:
            if st.button("Undo Last Entry ❌"):
                st.session_state.hour_slots.pop()
                # restore previous end
                if len(st.session_state.hour_slots) == 1:
                    st.session_state.hour_slots[0]["end_time"] = t2
                else:
                    st.session_state.hour_slots[-1]["end_time"] = "??:??"
                st.rerun()

    st.write("---")
    st.subheader("Add Next Hour Lord Transition")

    with st.form("hl_form"):
        col_h, col_m = st.columns(2)
        with col_h:
            next_hour = st.number_input("Hour (0–23)", 0, 23, value=0)
        with col_m:
            next_minute = st.number_input("Minute (0–59)", 0, 59, value=0)

        next_time = datetime.time(next_hour, next_minute)

        next_hl = st.selectbox("Hour Lord", ["Saturn","Jupiter","Mars","Sun","Venus","Mercury","Moon"])
        next_asc = st.selectbox("Ascendant", zodiac_cycle[:12])
        next_sat = st.selectbox("Saturn House", [str(i) for i in range(1,13)])
        next_chi = st.selectbox("Chiron House", [str(i) for i in range(1,13)])

        submit = st.form_submit_button("Add")

        if submit:
            last = st.session_state.hour_slots[-1]

            if next_time <= last["start_time"]:
                st.error("❗ New HL must be AFTER previous HL time.")
            else:
                # ✅ finalize previous slot end time
                last["end_time"] = next_time.strftime("%H:%M")

                # ✅ only update the **immediately previous slot's ranges**
                if next_asc not in last["asc_range"]:
                    last["asc_range"].append(next_asc)
                if next_sat not in last["sat_range"]:
                    last["sat_range"].append(next_sat)
                if next_chi not in last["chi_range"]:
                    last["chi_range"].append(next_chi)

                # ✅ create new slot with clean initial range
                st.session_state.hour_slots.append({
                    "hl": next_hl,
                    "start_time": next_time,
                    "end_time": "??:??",

                    "asc_start": next_asc,
                    "sat_start": next_sat,
                    "chi_start": next_chi,

                    "asc_range": [next_asc],
                    "sat_range": [next_sat],
                    "chi_range": [next_chi],

                    "alive": True
                })

                st.rerun()

    st.write("---")
    if st.button("Done — Go to Question Phase"):
        # ✅ ensure final slot has true end_time from step2
        st.session_state.hour_slots[-1]["end_time"] = t2
        st.success("Hour Lord setup complete.")
        st.session_state.step = 4
        st.rerun()

# ---------------------------
# STEP 4 — ASC Questions Based on Mars Sign
# ---------------------------
elif st.session_state.step == 4:

    st.header("ASC Questions Based on Mars Sign")
    st.write("There are no good or bad items.")
    st.write("If something feels uncomfortable but hits close to home, please mark **Yes**.")
    st.write("Trust your intuition — not every statement has to be perfectly accurate, but it should resonate.")
    
    # Your selected Mars sign
    mars = st.session_state.mars

    # import mars-asc dict
    from mars_asc_questions import mars_asc_questions

    # ✅ Extract only asc signs that exist in hour_slots
    possible_asc = sorted({
        asc
        for slot in st.session_state.hour_slots
        for asc in slot["asc_range"]
        if slot["alive"]
    })

    # ✅ Filter questions to only those asc
    questions = {asc: mars_asc_questions[mars][asc] for asc in possible_asc}

    # init state for answers
    if "asc_answers" not in st.session_state:
        st.session_state.asc_answers = {asc: None for asc in possible_asc}

    # Button Component
    def answer_button(label, asc, choice):
        selected = st.session_state.asc_answers.get(asc)
        is_active = (selected == choice)

        style = (
            "background-color:#4CAF50;color:white;border-radius:6px;padding:4px 10px;"
            if is_active else
            "background-color:#E8E8E8;color:black;border-radius:6px;padding:4px 10px;"
        )

        if st.button(label, key=f"{asc}_{label}", help=f"{asc} → {label}", use_container_width=False):
            st.session_state.asc_answers[asc] = choice

        st.markdown(f"<span style='{style}'></span>", unsafe_allow_html=True)


    st.markdown(f"### Mars: **{mars}**")

    # ASC questions loop
    for asc, q in questions.items():
        st.write(f"#### {asc}")
        st.write(q)

        col1, col2, col3 = st.columns(3)
        with col1:
            answer_button("Yes", asc, "Yes")
        with col2:
            answer_button("No", asc, "No")
        with col3:
            answer_button("Not Sure", asc, "Maybe")

        st.write("---")

    # ✅ Ensure all answered before allowing next step
    if None in st.session_state.asc_answers.values():
        st.warning("Please answer all questions before continuing.")
    else:
        if st.button("Continue to Hour-Lord × Asc Questions"):
            # elimination: drop asc marked "No"
            for asc, ans in st.session_state.asc_answers.items():
                if ans == "No":
                    # remove asc from all hour slots
                    for slot in st.session_state.hour_slots:
                        if asc in slot["asc_range"]:
                            slot["asc_range"].remove(asc)

            st.session_state.step = 5
            st.rerun()

# ---------------------------
# STEP 5 — Hour Lord × Asc Questions
# ---------------------------
elif st.session_state.step == 5:

    st.header("Hour Lord × Ascendant Questions")

    st.write("Even if it reflects the person you want to be, please select “No” if it doesn’t match your current reality.")

    from hourlord_asc_questions import hourlord_asc_questions

    # Initialize answer state
    if "hl_asc_answers" not in st.session_state:
        st.session_state.hl_asc_answers = {}

    # Render answer button
    def render_choice(slot_id, asc, value, label, color):
        key = f"HLASC_{slot_id}_{asc}"
        selected = st.session_state.hl_asc_answers.get(key)

        style = (
            f"background-color:{color};color:white;font-weight:bold;border-radius:8px;"
            f"padding:6px 14px;border:2px solid black;"
            if selected == value else
            "background-color:#EEEEEE;color:black;border-radius:8px;"
            "padding:6px 14px;border:1px solid #999;"
        )

        if st.button(label, key=f"{key}_{value}",
                     help=f"{asc} → {value}",
                     type="secondary" if selected != value else "primary"):
            st.session_state.hl_asc_answers[key] = value
            st.rerun()

        st.markdown(f"<style>#{key}_{value} {{{style}}}</style>", unsafe_allow_html=True)

    all_answered = True
    q_num = 0

    for slot_id, slot in enumerate(st.session_state.hour_slots):

        if not slot.get("alive", True):
            continue

        asc_list = slot.get("asc_range", [])

        # ✅ skip the slot entirely if no asc assigned
        if not asc_list:
            continue

        hl = slot["hl"]

        # ✅ take only the first ASC in the slot
        asc = asc_list[0]

        q_text = hourlord_asc_questions[hl][asc]

        q_num += 1
        st.subheader(f"**Question {q_num} — Hour Lord: {hl}**")
        st.markdown(f"**Active Ascendant:** {asc}")
        st.write(q_text)

        # Render buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            render_choice(slot_id, asc, "Yes", "✅ Yes", "#4CAF50")
        with col2:
            render_choice(slot_id, asc, "No", "❌ No", "#E74C3C")
        with col3:
            render_choice(slot_id, asc, "Maybe", "🤔 Not Sure", "#F4A100")

        st.write("---")

        # check answered
        key = f"HLASC_{slot_id}_{asc}"
        if key not in st.session_state.hl_asc_answers:
            all_answered = False

    # ✅ move on only if all answered
    if q_num == 0:
        st.info("No ASC questions available for selected range.")
        if st.button("Continue"):
            st.session_state.step = 6
            st.rerun()

    elif all_answered:
        if st.button("Continue to House Questions →"):
            st.session_state.step = 6
            st.rerun()
    else:
        st.info("Please answer all questions before continuing ✅")

# ---------------------------
# STEP 6 — Saturn + Chiron House Combined Questions (Deduped)
# ---------------------------
elif st.session_state.step == 6:

    st.header("Saturn & Chiron House Questions")
    st.write("If either Saturn or Chiron part feels false, choose **No**.")
    st.write("If unsure or mixed, choose **Not Sure**.")

    from house_questions import saturn_house_questions, chiron_house_questions

    slots = st.session_state.hour_slots

    unique_pairs = []
    slot_map = {}

    for idx, slot in enumerate(slots):
        if not slot["alive"]:
            continue
        pair = (slot["sat_start"], slot["chi_start"])
        if pair not in slot_map:
            slot_map[pair] = []
            unique_pairs.append(pair)
        slot_map[pair].append(idx)

    # ✅ store answers to pairs
    if "pair_answers" not in st.session_state:
        st.session_state.pair_answers = {}

    qnum = 1
    for sat, chi in unique_pairs:
        sat_q = saturn_house_questions.get(sat, "")
        chi_q = chiron_house_questions.get(chi, "")

        qkey = f"pair_{sat}_{chi}"
        st.markdown(f"### Question {qnum}")
        st.markdown(f"**Saturn House {sat}**\n{sat_q}")
        st.markdown(f"**Chiron House {chi}**\n{chi_q}")

        selected = st.session_state.pair_answers.get(qkey)

        cols = st.columns(3)
        if cols[0].button("✅ Yes", key=f"{qkey}_Yes"):
            st.session_state.pair_answers[qkey] = "Yes"
            st.rerun()
        if cols[1].button("❌ No", key=f"{qkey}_No"):
            st.session_state.pair_answers[qkey] = "No"
            st.rerun()
        if cols[2].button("🤔 Not Sure", key=f"{qkey}_Maybe"):
            st.session_state.pair_answers[qkey] = "Maybe"
            st.rerun()

        if selected:
            st.success(f"Selected: {selected}")
        st.write("---")
        qnum += 1

    if len(st.session_state.pair_answers) < len(unique_pairs):
        st.warning("Please answer all questions ✅")
    else:
        if st.button("Next: Results"):
            # apply NO = kill those slots
            for (sat, chi), idx_list in slot_map.items():
                key = f"pair_{sat}_{chi}"
                ans = st.session_state.pair_answers.get(key)
                if ans == "No":
                    for idx in idx_list:
                        slots[idx]["alive"] = False
            st.session_state.step = 7
            st.rerun()

# ---------------------------
# STEP 7 — Show Final Results (Pair filtering logic)
# ---------------------------
elif st.session_state.step == 7:
    st.header("🎯 Final Birth Window Results")

    alive_slots = [s for s in st.session_state.hour_slots if s["alive"]]

    st.subheader("⏰ Possible birth times based on your answers")
    for slot in alive_slots:
        st.write(
            f"{slot['start_time'].strftime('%H:%M')}–{slot['end_time']} "
            f"(HL: {slot['hl']}, "
            f"ASC: {', '.join(slot['asc_range'])}, "
            f"SAT: {', '.join(slot['sat_range'])}, "
            f"CHI: {', '.join(slot['chi_range'])})"
        )

    st.write("---")
    st.subheader("🧬 Natal Traits Based on Your Answers")

    asc_set = set()
    hl_set = set()
    approved_pairs = set()
    maybe_pairs = set()

    # ✅ read user decisions on SAT–CHI combos
    for key, val in st.session_state.pair_answers.items():
        _, s, c = key.split("_")
        if val == "Yes":
            approved_pairs.add((s, c))
        elif val == "Maybe":
            maybe_pairs.add((s, c))

    # ✅ collect only approved combos inside alive slots
    for slot in alive_slots:
        for asc in slot["asc_range"]:
            asc_set.add(asc)
        hl_set.add(slot["hl"])

    final_pairs = []
    for slot in alive_slots:
        for s in slot["sat_range"]:
            for c in slot["chi_range"]:
                if (s, c) in approved_pairs:
                    final_pairs.append((s, c))
                elif (s, c) in maybe_pairs:
                    final_pairs.append((s, c))

    # ✅ unique + sorted
    final_pairs = sorted(set(final_pairs), key=lambda x: (int(x[0]), int(x[1])))

    st.write(f"**Likely Ascendants:** {', '.join(sorted(asc_set))}")
    st.write(f"**Likely Hour Lords:** {', '.join(sorted(hl_set))}")

    st.write("**Likely Saturn–Chiron House Combinations:**")
    for s, c in final_pairs:
        st.write(f"- House {s} / House {c}")

    st.write("---")

    # ✅ CSV Download
    import pandas as pd
    slot_display = []
    for slot in st.session_state.hour_slots:
        slot_display.append({
            "start_time": slot['start_time'].strftime("%H:%M"),
            "end_time": slot['end_time'],
            "Hour Lord": slot['hl'],
            "Ascendant Range": ", ".join(slot['asc_range']),
            "Saturn House Range": ", ".join(slot['sat_range']),
            "Chiron House Range": ", ".join(slot['chi_range']),
            "Alive": slot['alive']
        })
    df_slots = pd.DataFrame(slot_display)
    st.download_button("📎 Download Analysis CSV", df_slots.to_csv(index=False), "birth_window_analysis.csv", "text/csv")

if "step" in st.session_state and st.session_state.step != 3:
    force_scroll_top()