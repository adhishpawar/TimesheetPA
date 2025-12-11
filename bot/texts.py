"""
bot/texts/responses.py - All bot message templates
Randomized friendly responses
"""

import random


# ============================================================================
# AUTHENTICATION RESPONSES
# ============================================================================

def reply_ask_username():
    """Prompt for username at start of login"""
    options = [
        "Hi 👋 I'm your Timesheet buddy. What's your username?",
        "Hello there! Let's log some work. Type your username to begin 😄",
        "Hey hey! Drop your username so I know who's working so hard."
    ]
    return random.choice(options)


def reply_ask_password(name: str):
    """Prompt for password after username"""
    options = [
        f"Nice to see you, {name}! Please enter your password 🔐",
        f"Hi {name}, password time… I promise I won't tell anyone 😉",
        f"{name}, type your password and we'll start logging magic."
    ]
    return random.choice(options)


def reply_login_success(name: str):
    """Successful login confirmation"""
    options = [
        f"Welcome back, {name}! 🚀 What did you work on?",
        f"Logged you in, {name} ✅ Tell me your work updates.",
        f"Authentication success for {name} 🎯 Share today's efforts!"
    ]
    return random.choice(options)


def reply_ask_invite():
    """Prompt for invite code (new user)"""
    options = [
        "Looks like you're new here 🤓 Please enter your invite code (ask your team lead if you don't have it).",
        "I don't know you yet 👀 Drop your invite code so we can become friends.",
        "New face! 😄 Type your invite code to complete onboarding."
    ]
    return random.choice(options)


def reply_invite_invalid():
    """Invalid or used invite code"""
    options = [
        "Hmm, that invite code didn't work 🙈 Try again or ping your admin.",
        "That code looks suspicious 🤨 double-check and send again.",
        "Invite code invalid or already used. Ask your team lead for a fresh one."
    ]
    return random.choice(options)


def reply_ask_display_name():
    """Prompt for full name during onboarding"""
    options = [
        "Cool! What's your full name? (I'll use it to greet you nicely 😇)",
        "Great, now tell me your name as you want it to appear in timesheets.",
        "Awesome! And your good name is…? 😄"
    ]
    return random.choice(options)


def reply_ask_new_password():
    """Prompt for password during onboarding"""
    options = [
        "Set a password for your timesheet login (keep it secret, keep it safe 🧙).",
        "Now choose a password. No pressure, but make it strong 💪",
        "Password time! Type the password you'll use to log in."
    ]
    return random.choice(options)


def reply_onboarding_done(name: str):
    """Onboarding complete, ready to log time"""
    options = [
        f"Welcome aboard, {name}! 🎉 You're all set—tell me what you worked on.",
        f"Onboarding complete ✅ Nice to meet you, {name}. Let's log some tasks.",
        f"Yay! {name}, your account is ready. What did you do today?"
    ]
    return random.choice(options)


# ============================================================================
# TIMESHEET ENTRY RESPONSES
# ============================================================================

def reply_need_hours():
    """Missing hours in entry"""
    options = [
        "I understood the task, but not the hours 🙈\nTry like: `today 4h testing mobile app`.",
        "Nice! But how many hours? 😅 Say it again with hours included (e.g. `3.5 hours`).",
        "Work detected ✅ Hours missing ❌\nTell me again with the number of hours."
    ]
    return random.choice(options)


def reply_need_task_description():
    """Missing task description"""
    options = [
        "I see ~3h of work, but what were you actually doing? 😄",
        "Hours spotted 👀 but no task. Tell me what you did in simple words.",
        "Nice! Now describe the work a bit, e.g. 'testing mobile app endpoints'."
    ]
    return random.choice(options)


def reply_need_project():
    """Missing project name"""
    options = [
        "Got it! Which project was this for? (e.g., Glovatrix, TeleInsight…)",
        "Cool. Before I save this, tell me the project name 😄",
        "Nice work! Just missing the project — which project should I tag this to?"
    ]
    return random.choice(options)


def reply_confirm_last_project(project: str):
    """Ask to confirm using last project"""
    options = [
        f"You didn't mention a project. Should I log this under **{project}** like your last entry? (yes/no or new project name)",
        f"Project missing 🤔 Last time you worked on **{project}**. Use the same project? (yes/no or type another)",
        f"Can I tag this to **{project}** again, or do you want a different project name?"
    ]
    return random.choice(options)


def reply_need_task_type():
    """Missing or unknown task type"""
    options = [
        "What type of work was this? Development, Testing, Debugging, Meeting, Research, Documentation, or DevOps?",
        "To categorize it better, pick one: Development / Testing / Debugging / Meeting / Research / Documentation / DevOps.",
        "One last thing 😅 — tell me the task type (Dev, Testing, Debugging, Meeting, etc.)."
    ]
    return random.choice(options)


def reply_saved(count: int):
    """Entry(ies) saved successfully"""
    options = [
        f"All set ✅ Logged {count} entry(ies).",
        f"Saved! 🧾 I've recorded {count} timesheet item(s) for you.",
        f"{count} entry(ies) safely tucked into the DB 💾"
    ]
    return random.choice(options)


# ============================================================================
# CORRECTION RESPONSES
# ============================================================================

def reply_correction_success(new_hours: float):
    """Successfully updated last entry"""
    options = [
        f"Done ✅ Updated your last entry to {new_hours}h.",
        f"Fixed it ✂️ last record now shows {new_hours} hours.",
        f"Correction applied – your last timesheet entry is {new_hours}h now."
    ]
    return random.choice(options)


def reply_correction_no_entry():
    """No previous entry to correct"""
    options = [
        "I tried, but you don't have any previous entries to correct 🤔",
        "No timesheet entries yet, so nothing to update 😅",
        "I'd love to correct something, but your timesheet is empty."
    ]
    return random.choice(options)
