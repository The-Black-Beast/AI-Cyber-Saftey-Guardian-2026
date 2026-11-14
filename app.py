import streamlit as st
import re
import csv
import os
from datetime import datetime
from urllib.parse import urlparse

# ============================================================
# AI CYBER SAFETY GUARDIAN
# Advanced Rule-Based Educational Prototype
# ============================================================

st.set_page_config(
    page_title="AI Cyber Safety Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM DESIGN
# ============================================================

st.markdown("""
<style>
.stApp {
    background-color: #071426;
    color: #F4F7FB;
}
[data-testid="stSidebar"] {
    background-color: #10243E;
}
h1, h2, h3 {
    color: #53C7F5 !important;
}
p, label, li {
    color: #E6EDF7;
}
div.stButton > button {
    background-color: #087EAA;
    color: white;
    border-radius: 9px;
    border: none;
    padding: 10px 20px;
    font-weight: bold;
}
div.stButton > button:hover {
    background-color: #0BA5D8;
    color: white;
}
[data-testid="stMetric"] {
    background-color: #10243E;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# DETECTION PARAMETERS AND RULES
# ============================================================

RULES = [
    {
        "name": "OTP Request",
        "category": "Sensitive Information",
        "pattern": r"\b(share|send|tell|provide|enter|confirm|verify)\b.{0,35}\b(otp|one[- ]time password|verification code)\b|\b(otp|one[- ]time password|verification code)\b.{0,35}\b(share|send|tell|provide)\b",
        "weight": 30,
        "advice": "Never share your OTP with anyone."
    },
    {
        "name": "Password Request",
        "category": "Sensitive Information",
        "pattern": r"\b(share|send|provide|enter|confirm|tell us)\b.{0,35}\b(password|passcode|login credentials)\b",
        "weight": 30,
        "advice": "Never share your password with unknown people."
    },
    {
        "name": "UPI PIN Request",
        "category": "Sensitive Information",
        "pattern": r"\b(share|enter|tell|provide|send)\b.{0,30}\bupi pin\b|\bupi pin\b.{0,30}\b(share|enter|tell|provide)\b",
        "weight": 35,
        "advice": "Never disclose your UPI PIN."
    },
    {
        "name": "Card Security Details",
        "category": "Banking Information",
        "pattern": r"\b(cvv|card number|debit card|credit card|expiry date)\b",
        "weight": 20,
        "advice": "Do not share card security information through messages."
    },
    {
        "name": "Bank Details Request",
        "category": "Banking Information",
        "pattern": r"\b(bank account details|account number|bank details|ifsc code)\b",
        "weight": 20,
        "advice": "Verify banking requests through official channels."
    },
    {
        "name": "KYC Information Request",
        "category": "Banking Information",
        "pattern": r"\b(kyc update|complete kyc|update your kyc|kyc verification|kyc expired)\b",
        "weight": 20,
        "advice": "Check KYC requests through your bank's official app or website."
    },
    {
        "name": "Payment Request",
        "category": "Financial Pressure",
        "pattern": r"\b(pay now|send money|transfer money|make payment|pay immediately|payment required)\b",
        "weight": 20,
        "advice": "Verify unexpected payment requests before paying."
    },
    {
        "name": "UPI Collect Request",
        "category": "Financial Pressure",
        "pattern": r"\b(upi collect|collect request|approve payment request|accept payment request)\b",
        "weight": 25,
        "advice": "Check every UPI collect request carefully before approving."
    },
    {
        "name": "Advance Fee",
        "category": "Financial Pressure",
        "pattern": r"\b(advance fee|processing fee|registration fee|release fee|pay fee to receive)\b",
        "weight": 25,
        "advice": "Be cautious of demands for advance payments."
    },
    {
        "name": "Prize Bait",
        "category": "Unrealistic Offers",
        "pattern": r"\b(you have won|you are winner|won a prize|lucky winner|lottery winner)\b",
        "weight": 20,
        "advice": "Verify unexpected prize claims independently."
    },
    {
        "name": "Guaranteed Reward",
        "category": "Unrealistic Offers",
        "pattern": r"\b(guaranteed reward|guaranteed prize|free gift|claim your reward|cash prize)\b",
        "weight": 15,
        "advice": "Be careful with unexpected reward offers."
    },
    {
        "name": "Easy Earning Offer",
        "category": "Unrealistic Offers",
        "pattern": r"\b(earn money easily|daily income|work from home|instant income|double your money)\b",
        "weight": 15,
        "advice": "Verify job and earning offers before sharing information."
    },
    {
        "name": "Urgent Language",
        "category": "Manipulation",
        "pattern": r"\b(urgent|immediately|act now|last chance|within 24 hours|today only|hurry up)\b",
        "weight": 10,
        "advice": "Do not let urgent messages pressure you into acting quickly."
    },
    {
        "name": "Threatening Language",
        "category": "Manipulation",
        "pattern": r"\b(account blocked|account suspended|legal action|police case|account will be closed|service discontinued)\b",
        "weight": 20,
        "advice": "Verify threats through the organisation's official contact details."
    },
    {
        "name": "Secrecy Request",
        "category": "Manipulation",
        "pattern": r"\b(keep this secret|do not tell anyone|don't tell anyone|confidential transaction|tell nobody)\b",
        "weight": 15,
        "advice": "Be cautious when someone asks you to hide a transaction."
    },
    {
        "name": "Possible Impersonation",
        "category": "Identity Warning",
        "pattern": r"\b(bank officer|customer care executive|government officer|support team|official representative)\b",
        "weight": 10,
        "advice": "Verify the sender's identity independently."
    },
    {
        "name": "Shortened Link",
        "category": "Suspicious Links",
        "pattern": r"\b(bit\.ly|tinyurl\.com|t\.co|goo\.gl|shorturl\.at|cutt\.ly|is\.gd)/",
        "weight": 20,
        "advice": "Avoid opening unexpected shortened links."
    },
    {
        "name": "APK Installation Request",
        "category": "Device Safety",
        "pattern": r"\b(install apk|download apk|install this application|unknown app|download this app)\b",
        "weight": 25,
        "advice": "Do not install applications from unverified sources."
    },
    {
        "name": "Remote Access Request",
        "category": "Device Safety",
        "pattern": r"\b(remote access|screen sharing app|anydesk|teamviewer|control your phone|access your device)\b",
        "weight": 30,
        "advice": "Never give unknown people remote access to your device."
    },
    {
        "name": "QR Payment Request",
        "category": "Payment Warning",
        "pattern": r"\b(scan qr|scan this qr|qr code to receive|scan and claim|scan to get money)\b",
        "weight": 20,
        "advice": "Verify QR-code payment requests before scanning."
    },
    {
        "name": "Gaming Wallet Context",
        "category": "Gaming Warning",
        "pattern": r"\b(gaming wallet|game wallet|wallet recharge|game deposit|gaming account balance)\b",
        "weight": 10,
        "advice": "Verify gaming wallet transactions through the official platform."
    },
    {
        "name": "Gaming Reward Offer",
        "category": "Gaming Warning",
        "pattern": r"\b(free gaming reward|game prize|gaming bonus|free game coins|winning game reward)\b",
        "weight": 15,
        "advice": "Be cautious of unexpected gaming rewards and payment demands."
    }
]

CRITICAL_RULES = {
    "OTP Request",
    "Password Request",
    "UPI PIN Request",
    "Remote Access Request"
}


# ============================================================
# URL ANALYSIS ENGINE
# ============================================================

def analyse_url(message):

    findings = []

    urls = re.findall(
        r"(?:https?://|www\.)[^\s]+",
        message,
        flags=re.IGNORECASE
    )

    for raw_url in urls:

        clean_url = raw_url.rstrip(".,!?;:)")

        if clean_url.lower().startswith("www."):
            clean_url = "http://" + clean_url

        try:
            parsed = urlparse(clean_url)
            domain = parsed.hostname or ""

            if parsed.scheme == "http":
                findings.append(
                    "URL uses HTTP instead of HTTPS"
                )

            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", domain):
                findings.append(
                    "URL contains a numeric IP address"
                )

            if "@" in parsed.netloc:
                findings.append(
                    "URL contains an unusual @ symbol"
                )

            if "xn--" in domain:
                findings.append(
                    "URL contains possible punycode characters"
                )

            if len(domain) > 35:
                findings.append(
                    "URL has an unusually long domain name"
                )

            if domain.count(".") >= 3:
                findings.append(
                    "URL contains multiple subdomains"
                )

            unusual_extensions = (
                ".click", ".top", ".xyz", ".work",
                ".buzz", ".live", ".loan"
            )

            if domain.endswith(unusual_extensions):
                findings.append(
                    "URL uses a less-familiar domain extension"
                )

        except Exception:
            findings.append(
                "URL could not be analysed properly"
            )

    return list(dict.fromkeys(findings))


# ============================================================
# MESSAGE SCANNING ENGINE
# ============================================================

def scan_message(message):

    score = 0
    detected_rules = []
    advice_list = []

    for rule in RULES:

        if re.search(
            rule["pattern"],
            message,
            flags=re.IGNORECASE
        ):

            detected_rules.append(rule)
            score += rule["weight"]
            advice_list.append(rule["advice"])

    url_findings = analyse_url(message)

    for finding in url_findings:
        score += 10
        advice_list.append(
            "Check links carefully before opening them."
        )

    score = min(score, 100)

    critical_detected = any(
        rule["name"] in CRITICAL_RULES
        for rule in detected_rules
    )

    if critical_detected:
        score = max(score, 70)

    if score >= 70:
        level = "HIGH RISK"
    elif score >= 35:
        level = "MEDIUM RISK"
    else:
        level = "LOWER INDICATED RISK"

    if not detected_rules and not url_findings:
        advice_list.append(
            "No programmed warning pattern was detected. "
            "This does not guarantee that the message is safe."
        )

    advice_list = list(dict.fromkeys(advice_list))

    return (
        score,
        level,
        detected_rules,
        url_findings,
        advice_list
    )


# ============================================================
# CYBER SAFETY QUIZ DATA
# ============================================================

QUIZ = [

    {
        "question": "You receive a message claiming your bank account will be blocked unless you click a link and update KYC. What should you do?",
        "options": [
            "Click the link immediately",
            "Share your banking information",
            "Verify the message through official bank channels",
            "Forward the message to everyone"
        ],
        "answer": 2,
        "explanation": "Always verify banking messages through official channels."
    },

    {
        "question": "A website displays your bank's logo. Does that prove the website is genuine?",
        "options": [
            "Yes, logos always prove authenticity",
            "No, logos can be copied",
            "Yes, if the website has colourful design",
            "No, because all websites are unsafe"
        ],
        "answer": 1,
        "explanation": "A logo can be copied. Check the website address carefully."
    },

    {
        "question": "Which of the following are warning signs? Select all correct answers.",
        "options": [
            "A stranger asks for your UPI PIN",
            "Someone asks you to install a remote-access app",
            "An unknown person sends a UPI collect request",
            "You check a bank notice through its official app"
        ],
        "answer": [0, 1, 2],
        "multi": True,
        "explanation": "Unexpected requests for payment credentials, remote access, and payment approval are warning signs."
    },

    {
        "question": "A suspicious message can be dangerous even if it does not contain obvious scam keywords.",
        "options": [
            "True",
            "False"
        ],
        "answer": 0,
        "explanation": "Some suspicious messages use ordinary language. Always check the context and sender."
    },

    {
        "question": "Someone asks you to share an OTP to receive a prize. What is the safest action?",
        "options": [
            "Share the OTP",
            "Ask for more prizes",
            "Do not share the OTP",
            "Send your password too"
        ],
        "answer": 2,
        "explanation": "An OTP should remain private."
    },

    {
        "question": "An unknown message asks you to scan a QR code to receive a prize. What should you do?",
        "options": [
            "Scan it immediately",
            "Verify the offer first",
            "Share the QR code with friends",
            "Enter your UPI PIN"
        ],
        "answer": 1,
        "explanation": "Unexpected QR-code payment instructions should be treated cautiously."
    },

    {
        "question": "The scanner gives a message a risk score of 90. What does that mean?",
        "options": [
            "There is exactly a 90% chance of fraud",
            "The message is definitely genuine",
            "The programmed warning indicators produced a high score",
            "The message has been checked by the police"
        ],
        "answer": 2,
        "explanation": "The score is a rule-based indicator, not a statistical probability."
    },

    {
        "question": "Which statements about website links are correct? Select all correct answers.",
        "options": [
            "HTTPS alone guarantees that a website is genuine",
            "Shortened links can hide the final destination",
            "A familiar logo proves that a website is safe",
            "The domain name should be checked carefully"
        ],
        "answer": [1, 3],
        "multi": True,
        "explanation": "HTTPS and logos do not guarantee legitimacy. Check the actual domain."
    },

    {
        "question": "An unknown person asks you to install an APK file sent through a message. What should you do?",
        "options": [
            "Install it immediately",
            "Avoid installing it and verify the source",
            "Share it with classmates",
            "Disable all phone security"
        ],
        "answer": 1,
        "explanation": "Avoid installing applications from unverified sources."
    },

    {
        "question": "What is the main working method of this project?",
        "options": [
            "It guarantees detection of every scam",
            "It uses programmed rules and pattern matching",
            "It automatically contacts the police",
            "It verifies every sender's identity"
        ],
        "answer": 1,
        "explanation": "This educational prototype uses predefined rules, regular expressions, URL checks, and a weighted scoring system."
    }

]

# ============================================================
# ============================================================
# SESSION STATE
# ============================================================

if "last_scan" not in st.session_state:
    st.session_state.last_scan = None

if "quiz_attempt" not in st.session_state:
    st.session_state.quiz_attempt = 1

if "quiz_result" not in st.session_state:
    st.session_state.quiz_result = None


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

st.sidebar.title("🛡️ Cyber Safety Guardian")
st.sidebar.caption("Digital Protection and Awareness")

page = st.sidebar.radio(
    "NAVIGATION MENU",
    [
        "Dashboard",
        "Message Scanner",
        "Detection Parameters",
        "Cyber Safety Guide",
        "Safety Quiz",
        "Project Reviews",
        "About & Limitations"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "Educational prototype for identifying "
    "possible suspicious-message indicators."
)


# ============================================================
# COMMON HEADER
# ============================================================

st.title("🛡️ AI CYBER SAFETY GUARDIAN")
st.caption(
    "An educational rule-based prototype for suspicious "
    "message analysis and cyber-safety awareness."
)

st.markdown("---")


# ============================================================
# PAGE 1: DASHBOARD
# ============================================================

if page == "Dashboard":

    st.header("Welcome to the Cyber Safety Dashboard")

    st.write(
        "The AI Cyber Safety Guardian is designed to help users "
        "recognise possible warning signs in suspicious messages. "
        "It analyses message text, checks programmed detection "
        "patterns, examines basic URL structures, and calculates "
        "a risk score."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Detection Rules", len(RULES))

    with col2:
        st.metric("Quiz Questions", len(QUIZ))

    with col3:
        st.metric("Review Parameters", 10)

    st.markdown("## Main Features")

    features = [
        ("Message Scanner", "Analyses text for suspicious indicators."),
        ("Risk Scoring", "Calculates a score from detected warning signs."),
        ("URL Analysis", "Checks basic structural characteristics of links."),
        ("Cyber Safety Guide", "Provides useful online safety guidance."),
        ("Interactive Quiz", "Tests knowledge through 10 questions."),
        ("Project Reviews", "Collects ratings from judges and visitors.")
    ]

    for feature, description in features:
        with st.container(border=True):
            st.subheader(feature)
            st.write(description)

    st.markdown("## How the System Works")

    st.write("1. The user enters a message.")
    st.write("2. The scanner checks the message against programmed rules.")
    st.write("3. Suspicious indicators are identified.")
    st.write("4. Basic URL checks are performed where applicable.")
    st.write("5. A weighted risk score is calculated.")
    st.write("6. The result and safety recommendations are displayed.")

    st.warning(
        "A low risk score does not prove that a message is safe. "
        "The scanner may miss scams or flag legitimate messages."
    )


# ============================================================
# PAGE 2: MESSAGE SCANNER
# ============================================================

elif page == "Message Scanner":

    st.header("📩 Suspicious Message Scanner")

    st.write(
        "Enter a fictional or redacted message below. "
        "Do not enter real OTPs, passwords, private links, "
        "or confidential banking information."
    )

    message = st.text_area(
        "Enter the message to analyse:",
        height=180,
        placeholder=(
            "Example: Your account needs verification. "
            "Click this link and share your OTP."
        )
    )

    analyse = st.button(
        "🔍 Analyse Message",
        use_container_width=True
    )

    if analyse:

        if not message.strip():

            st.error("Please enter a message first.")

        else:

            score, level, hits, url_findings, advice = (
                scan_message(message)
            )

            st.session_state.last_scan = {
                "time": datetime.now().strftime(
                    "%d-%m-%Y %H:%M:%S"
                ),
                "score": score,
                "level": level,
                "hits": hits,
                "url_findings": url_findings,
                "advice": advice
            }

    if st.session_state.last_scan is not None:

        result = st.session_state.last_scan

        st.markdown("---")
        st.subheader("Analysis Result")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Risk Score",
                str(result["score"]) + " / 100"
            )

        with col2:
            st.metric(
                "Risk Classification",
                result["level"]
            )

        st.progress(result["score"] / 100)

        if result["level"] == "HIGH RISK":
            st.error(
                "High number of programmed warning indicators detected."
            )

        elif result["level"] == "MEDIUM RISK":
            st.warning(
                "Some suspicious indicators were detected."
            )

        else:
            st.success(
                "Fewer programmed warning indicators were detected. "
                "This does not guarantee safety."
            )

        st.markdown("### Detected Warning Indicators")

        if result["hits"]:

            for rule in result["hits"]:

                with st.container(border=True):
                    st.markdown(
                        "*" + rule["name"] + "*"
                    )
                    st.caption(
                        "Category: " + rule["category"]
                    )
                    st.write(rule["advice"])

        else:

            st.info(
                "No programmed text detection rule was triggered."
            )

        st.markdown("### URL Analysis")

        if result["url_findings"]:

            for finding in result["url_findings"]:
                st.warning(finding)

        else:

            st.info(
                "No URL structural warning was identified."
            )

        st.markdown("### Safety Recommendations")

        for advice_item in result["advice"]:
            st.write("• " + advice_item)

        st.caption(
            "Last analysed: " + result["time"]
        )

        st.caption(
            "The score is a heuristic based on programmed rules, "
            "not a probability of fraud."
        )

        if st.button("Clear Previous Result"):
            st.session_state.last_scan = None
            st.rerun()


# ============================================================
# PAGE 3: DETECTION PARAMETERS
# ============================================================

elif page == "Detection Parameters":

    st.header("⚙️ Detection Parameters")

    st.write(
        "This section explains the programmed indicators "
        "used by the message-scanning engine."
    )

    categories = sorted(
        set(rule["category"] for rule in RULES)
    )

    selected_category = st.selectbox(
        "Select a detection category:",
        ["All Categories"] + categories
    )

    filtered_rules = RULES

    if selected_category != "All Categories":

        filtered_rules = [
            rule for rule in RULES
            if rule["category"] == selected_category
        ]

    st.markdown(
        "**Number of displayed rules: "
        + str(len(filtered_rules))
        + "**"
    )

    for index, rule in enumerate(filtered_rules, start=1):

        with st.expander(
            str(index) + ". " + rule["name"]
        ):

            st.write(
                "*Category:* " + rule["category"]
            )

            st.write(
                "*Detection weight:* "
                + str(rule["weight"])
            )

            st.write(
                "*Safety recommendation:* "
                + rule["advice"]
            )

    st.markdown("---")

    st.subheader("How Risk Scoring Works")

    st.write(
        "Each detection rule has a programmed weight. "
        "When a message matches a rule, its weight contributes "
        "to the total risk score. URL warning indicators may "
        "also contribute to the score."
    )

    st.write("*Risk classification used by this prototype:*")

    st.write("- 0–34: Lower Indicated Risk")
    st.write("- 35–69: Medium Risk")
    st.write("- 70–100: High Risk")

    st.info(
        "These categories are prototype thresholds. "
        "They are not official fraud classifications."
    )


# ============================================================
# PAGE 4: CYBER SAFETY GUIDE
# ============================================================

elif page == "Cyber Safety Guide":

    st.header("📚 Cyber Safety Guide")

    st.write(
        "Follow these basic practices to protect your "
        "personal information and digital accounts."
    )

    safety_topics = [

        (
            "1. Protect Your OTP",
            [
                "Never share OTPs with unknown people.",
                "Do not disclose verification codes over calls or messages.",
                "Be careful with unexpected account-verification requests."
            ]
        ),

        (
            "2. Protect Your Passwords",
            [
                "Use strong and unique passwords.",
                "Never share your password with strangers.",
                "Use two-factor authentication where available."
            ]
        ),

        (
            "3. Stay Safe While Making Digital Payments",
            [
                "Never share your UPI PIN.",
                "Check payment requests before approving them.",
                "Verify the recipient before transferring money."
            ]
        ),

        (
            "4. Recognise Suspicious Messages",
            [
                "Be cautious of unexpected prize messages.",
                "Check urgent requests carefully.",
                "Verify the sender through official channels."
            ]
        ),

        (
            "5. Avoid Suspicious Links",
            [
                "Check the domain name before opening a link.",
                "Avoid unexpected shortened links.",
                "Do not enter personal information on unknown websites."
            ]
        ),

        (
            "6. Protect Your Device",
            [
                "Install applications from trusted sources.",
                "Avoid unknown APK files.",
                "Do not provide remote access to unknown people."
            ]
        ),

        (
            "7. Be Careful with QR Codes",
            [
                "Check the payment details before approving a transaction.",
                "Do not scan unknown QR codes to claim unexpected rewards.",
                "Remember that receiving money does not normally require sharing your UPI PIN."
            ]
        ),

        (
            "8. Protect Your Personal Information",
            [
                "Avoid sharing confidential information publicly.",
                "Do not send identity documents to unknown contacts.",
                "Use privacy settings on digital platforms."
            ]
        ),

        (
            "9. Verify Before Trusting",
            [
                "Contact organisations using official contact details.",
                "Do not rely only on a logo or display name.",
                "Take time to verify unusual requests."
            ]
        ),

        (
            "10. Report Suspicious Activity",
            [
                "Keep records of suspicious communications.",
                "Inform a trusted adult or appropriate authority.",
                "In India, cybercrime complaints can be reported through the official government cybercrime portal."
            ]
        )
    ]

    for title, tips in safety_topics:

        with st.expander(title):

            for tip in tips:
                st.write("• " + tip)

    st.markdown("---")

    st.subheader("Remember")

    st.success(
        "STOP – THINK – VERIFY – ACT SAFELY"
    )

    st.write(
        "Never allow fear, urgency, or attractive offers "
        "to pressure you into sharing confidential information."
    )


# ============================================================
# PAGE 5: INTERACTIVE SAFETY QUIZ
# ============================================================

elif page == "Safety Quiz":

    st.header("🧠 Interactive Cyber Safety Quiz")

    st.write(
        "Test your understanding of cyber safety with "
        "these 10 questions."
    )

    st.caption(
        "Some questions require selecting more than one answer."
    )

    attempt = st.session_state.quiz_attempt

    with st.form("cyber_safety_quiz_form"):

        quiz_answers = []

        for i, question in enumerate(QUIZ):

            st.markdown(
                "### Question "
                + str(i + 1)
                + " of "
                + str(len(QUIZ))
            )

            st.write(question["question"])

            widget_key = (
                "quiz_"
                + str(attempt)
                + "_"
                + str(i)
            )

            if question.get("multi", False):

                answer = st.multiselect(
                    "Select all correct answers:",
                    question["options"],
                    default=[],
                    key=widget_key
                )

            else:

                answer = st.radio(
                    "Choose one answer:",
                    question["options"],
                    index=None,
                    key=widget_key
                )

            quiz_answers.append(answer)

            st.markdown("---")

        submitted = st.form_submit_button(
            "Submit Quiz",
            use_container_width=True
        )

    if submitted:

        missing = []

        for i, answer in enumerate(quiz_answers):

            if answer is None or answer == []:

                missing.append(i + 1)

        if missing:

            st.warning(
                "Please answer all questions before submitting. "
                "Unanswered question numbers: "
                + ", ".join(map(str, missing))
            )

        else:

            score = 0
            details = []

            for i, question in enumerate(QUIZ):

                if question.get("multi", False):

                    expected = {
                        question["options"][index]
                        for index in question["answer"]
                    }

                    correct = (
                        set(quiz_answers[i]) == expected
                    )

                    correct_answer_text = ", ".join(
                        sorted(expected)
                    )

                else:

                    expected = question["options"][
                        question["answer"]
                    ]

                    correct = (
                        quiz_answers[i] == expected
                    )

                    correct_answer_text = expected

                if correct:
                    score += 1

                details.append({
                    "question": question["question"],
                    "your_answer": quiz_answers[i],
                    "correct_answer": correct_answer_text,
                    "correct": correct,
                    "explanation": question["explanation"]
                })

            st.session_state.quiz_result = {
                "score": score,
                "details": details
            }

    if st.session_state.quiz_result is not None:

        result = st.session_state.quiz_result

        st.markdown("---")
        st.subheader("Your Quiz Result")

        st.metric(
            "Your Score",
            str(result["score"]) + " / 10"
        )

        st.progress(result["score"] / 10)

        percentage = result["score"] * 10

        if percentage >= 90:
            st.success("Outstanding! Excellent cyber-safety knowledge.")

        elif percentage >= 70:
            st.success("Very good! You understand many safety practices.")

        elif percentage >= 50:
            st.warning("Good effort. Keep learning about cyber safety.")

        else:
            st.info("Keep practising. Review the Cyber Safety Guide.")

        st.markdown("### Answer Review")

        for index, detail in enumerate(
            result["details"],
            start=1
        ):

            with st.expander(
                "Question " + str(index)
            ):

                st.write(detail["question"])

                if detail["correct"]:
                    st.success("Your answer is correct.")

                else:
                    st.error("Your answer is incorrect.")

                st.write(
                    "*Your answer:* "
                    + str(detail["your_answer"])
                )

                st.write(
                    "*Correct answer:* "
                    + detail["correct_answer"]
                )

                st.info(detail["explanation"])

        if st.button("Retake Quiz"):

            st.session_state.quiz_attempt += 1
            st.session_state.quiz_result = None
            st.rerun()


# ============================================================

# ============================================================
# PAGE 6: PROJECT REVIEWS
# ============================================================

elif page == "Project Reviews":

    st.header("⭐ PROJECT EVALUATION")
    st.subheader("Judge's Marking Panel")

    st.write(
        "Evaluate the AI Cyber Safety Guardian "
        "by giving marks for each parameter."
    )

    reviewer = st.text_input(
        "Judge / Reviewer Name"
    )

    parameters = [
        "Dashboard Design",
        "Message Scanner",
        "Detection Parameters",
        "Practical Demonstration",
        "Cyber Safety Guide",
        "Interactive Safety Quiz",
        "User Interface and Navigation",
        "Risk Scoring System",
        "Innovation and Usefulness",
        "Overall Presentation"
    ]

    st.markdown("---")

    marks = {}

    for i, parameter in enumerate(parameters):

        st.markdown("### " + str(i+1) + ". " + parameter)

        marks[parameter] = st.slider(
            "Give marks (0–10)",
            min_value=0,
            max_value=10,
            value=5,
            key="judge_mark_" + str(i)
        )

        st.caption(
            "Marks awarded: "
            + str(marks[parameter])
            + " / 10"
        )

        st.markdown("---")

    total = sum(marks.values())

    if total >= 90:
        rating = "Outstanding"
    elif total >= 80:
        rating = "Excellent"
    elif total >= 70:
        rating = "Very Good"
    elif total >= 60:
        rating = "Good"
    elif total >= 50:
        rating = "Average"
    elif total >= 35:
        rating = "Bad"
    else:
        rating = "Very Bad"

    st.subheader("Evaluation Summary")

    st.metric(
        "TOTAL MARKS",
        str(total) + " / 100"
    )

    st.metric(
        "OVERALL RATING",
        rating
    )

    st.progress(total / 100)

    feedback = st.text_area(
        "Judge's Suggestions / Feedback",
        placeholder="Enter your comments here..."
    )

    if st.button(
        "Submit Final Evaluation",
        use_container_width=True
    ):

        review_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "reviews.csv"
        )

        try:

            file_exists = os.path.exists(review_file)

            with open(
                review_file,
                "a",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                if not file_exists or os.path.getsize(review_file) == 0:

                    writer.writerow(
                        ["Date", "Reviewer"]
                        + parameters
                        + ["Total", "Rating", "Feedback"]
                    )

                writer.writerow(
                    [
                        datetime.now().strftime(
                            "%d-%m-%Y %H:%M:%S"
                        ),
                        reviewer
                    ]
                    + [marks[p] for p in parameters]
                    + [total, rating, feedback]
                )

            st.success(
                "Evaluation submitted successfully!"
            )

        except Exception as error:

            st.error(
                "Could not save the evaluation: "
                + str(error)
            )

# ============================================================
# PAGE 7: ABOUT AND LIMITATIONS
# ============================================================

elif page == "About & Limitations":

    st.header("ℹ️ About AI Cyber Safety Guardian")

    st.write(
        "AI Cyber Safety Guardian is an educational cyber-safety "
        "project developed using Python and Streamlit. "
        "It demonstrates how programmed rules and text-pattern "
        "matching can help identify possible warning signs "
        "in suspicious digital messages."
    )

    st.subheader("Project Objectives")

    objectives = [
        "To spread awareness about online scams and digital fraud.",
        "To identify common suspicious patterns in messages.",
        "To encourage safe online payment practices.",
        "To protect users from sharing confidential information.",
        "To demonstrate a practical Python-based application.",
        "To promote responsible digital behaviour."
    ]

    for objective in objectives:
        st.write("• " + objective)

    st.markdown("---")

    st.subheader("Technology Used")

    technologies = [
        ("Python", "Main programming language."),
        ("Streamlit", "Used to create the interactive web application."),
        ("Regular Expressions", "Used to identify programmed text patterns."),
        ("CSV", "Used to store project reviews."),
        ("URL Parsing", "Used for basic URL structure analysis.")
    ]

    for technology, description in technologies:

        with st.container(border=True):

            st.markdown("*" + technology + "*")
            st.write(description)

    st.markdown("---")

    st.subheader("How Is This Project Different?")

    st.write(
        "This project demonstrates a separate educational "
        "message-analysis interface. Instead of relying only "
        "on a telecom provider's spam label, it displays "
        "individual warning indicators, explains the detection "
        "categories, calculates a rule-based score, and provides "
        "safety recommendations."
    )

    st.markdown("---")

    st.subheader("Project Limitations")

    limitations = [
        "This is a rule-based prototype, not a trained AI or machine-learning model.",
        "It uses predefined text patterns and regular expressions.",
        "It cannot guarantee detection of every scam message.",
        "Some genuine messages may trigger warnings.",
        "Some fraudulent messages may not match the programmed rules.",
        "It does not verify the real identity of the sender.",
        "It does not visit links or check live website reputation.",
        "Its risk score is a heuristic, not a probability of fraud.",
        "It does not automatically contact banks, telecom providers, or law-enforcement agencies."
    ]

    for limitation in limitations:
        st.write("• " + limitation)

    st.warning(
        "Always verify suspicious messages independently. "
        "Do not rely on this prototype as the only method "
        "of deciding whether a message is safe."
    )

    st.markdown("---")

    st.subheader("Project Message")

    st.success(
        "STOP • THINK • VERIFY • STAY SAFE"
    )

    st.write(
        "A little awareness can help prevent major digital risks. "
        "Think before you click, verify before you trust, "
        "and never share confidential information."
    )


# ============================================================
# COMMON FOOTER
# ============================================================

st.markdown("---")

st.markdown(
    """
    <div style="text-align:center; padding:15px;">
        <h3>🛡️ AI CYBER SAFETY GUARDIAN</h3>
        <p>Digital Awareness • Online Protection • Safer Internet</p>
        <p>Educational Rule-Based Prototype</p>
    </div>
    """,
    unsafe_allow_html=True
)

st.caption(
    "This application is an educational demonstration. "
    "Its results are not a guarantee of message safety."
)

# ============================================================
# END OF PROJECT CODE
# ============================================================
