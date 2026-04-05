"""
script_gen.py — converts a user prompt + target duration into scene dicts.

Each scene: {visual_prompt: str, voiceover: str, duration_sec: float}

The number of scenes and per-scene duration are calculated from target_duration_sec:
  - 8 scenes minimum, 12 maximum
  - per_scene_duration = target_duration_sec / num_scenes
  - voiceover length scales with scene duration (~2.3 words/sec at 145 WPM)
"""

# Average speaking rate at pyttsx3 rate=145: ~2.3 words per second
WORDS_PER_SECOND = 2.3


def _words_for_duration(seconds: float) -> int:
    """Return target word count for a given scene duration."""
    return max(8, int(seconds * WORDS_PER_SECOND))


def generate_script(prompt: str, target_duration_sec: float = 120.0) -> list:
    """
    Generate a list of scene dicts from a user prompt and target video duration.

    Args:
        prompt: user's video description
        target_duration_sec: total desired video length in seconds (default: 120 = 2 min)

    Returns:
        list of dicts: [{visual_prompt, voiceover, duration_sec}, ...]
    """
    p = prompt.lower()

    # Detect video type
    if any(w in p for w in ['marketing', 'reel', 'saas', 'product', 'brand',
                             'ad', 'advertisement', 'startup', 'business']):
        template_key = 'marketing'
    elif any(w in p for w in ['educational', 'tutorial', 'explain', 'how to',
                               'learn', 'course', 'teach', 'guide']):
        template_key = 'educational'
    elif any(w in p for w in ['social', 'tiktok', 'shorts', 'viral',
                               'instagram', 'youtube', 'faceless']):
        template_key = 'social'
    else:
        template_key = 'marketing'

    # Extract subject from prompt
    subject = prompt
    for prefix in ['create a', 'make a', 'generate a', 'build a', 'produce a',
                   'create', 'make', 'generate', 'build', 'produce']:
        if p.startswith(prefix):
            subject = prompt[len(prefix):].strip()
            break

    # Calculate scene count and per-scene duration
    # 8 scenes for short videos, up to 12 for longer ones
    if target_duration_sec <= 60:
        num_scenes = 5
    elif target_duration_sec <= 180:
        num_scenes = 8
    elif target_duration_sec <= 300:
        num_scenes = 10
    else:
        num_scenes = 12

    per_scene_sec = target_duration_sec / num_scenes
    target_words = _words_for_duration(per_scene_sec)

    s = subject  # short alias for visual prompts

    # Full voiceover blocks — long enough for any duration
    # Each entry is a (short_version, extended_version) tuple
    # We pick the right length based on target_words
    scene_templates = {
        'marketing': [
            {
                'visual_prompt': (
                    f'cinematic establishing shot, modern tech startup office, floor-to-ceiling windows, '
                    f'city skyline, golden hour lighting, professional atmosphere, {s}, photorealistic, 8k'
                ),
                'voiceover_long': (
                    f'The way businesses operate is changing forever. '
                    f'In every industry, across every market, the companies that adapt are the ones that win. '
                    f'The question is not whether change is coming — it is already here. '
                    f'And the businesses embracing it today are pulling so far ahead, '
                    f'the gap is becoming impossible to close.'
                ),
                'voiceover_short': 'The way businesses operate is changing forever.',
            },
            {
                'visual_prompt': (
                    f'close up frustrated professional surrounded by paperwork and spreadsheets, '
                    f'messy desk, stressed expression, dramatic cinematic shadows, {s}'
                ),
                'voiceover_long': (
                    f'Endless manual tasks. Slow processes. Costly mistakes that keep happening again and again. '
                    f'Your team is talented, but they are spending most of their time on work '
                    f'that should never touch a human hand. '
                    f'Every hour lost to repetitive tasks is an hour not spent on strategy, '
                    f'on growth, on the work that actually moves your business forward.'
                ),
                'voiceover_short': 'Endless manual tasks and slow processes are holding your business back.',
            },
            {
                'visual_prompt': (
                    f'sleek AI dashboard on large curved monitor, real-time data flowing, '
                    f'glowing blue interface, futuristic clean UI, {s}, ultra detailed, 8k'
                ),
                'voiceover_long': (
                    f'Our AI automation platform changes everything. '
                    f'It learns your workflows, handles your repetitive tasks, '
                    f'and integrates seamlessly with the tools your team already uses. '
                    f'From data entry to customer follow-ups, from reporting to scheduling — '
                    f'the platform handles it all, faster and more accurately than any human could. '
                    f'And it gets smarter every single day.'
                ),
                'voiceover_short': 'Our AI platform automates everything so your team can focus on what matters.',
            },
            {
                'visual_prompt': (
                    f'diverse business team celebrating success around conference table, '
                    f'upward trending charts on screen, modern bright office, professional lighting, {s}'
                ),
                'voiceover_long': (
                    f'Our customers are saving an average of twenty hours every week per team member. '
                    f'That is five hundred hours a year, per person, redirected to high-value work. '
                    f'They are closing deals faster, responding to customers quicker, '
                    f'and scaling their operations without scaling their headcount. '
                    f'The results speak for themselves — revenue up, costs down, teams happier.'
                ),
                'voiceover_short': 'Join thousands of businesses saving twenty hours every week with AI.',
            },
            {
                'visual_prompt': (
                    f'split screen: traditional vs AI-powered workflow comparison, '
                    f'before and after transformation visual, dramatic contrast, {s}, cinematic'
                ),
                'voiceover_long': (
                    f'Think about where your business could be six months from now '
                    f'if your team was not buried in manual work. '
                    f'Think about the deals you could close, the customers you could serve, '
                    f'the products you could build. '
                    f'That future is not years away. It is available to you right now, '
                    f'with a single decision to automate what should never have been manual.'
                ),
                'voiceover_short': 'Imagine what your team could achieve without manual work holding them back.',
            },
            {
                'visual_prompt': (
                    f'customer success stories montage, testimonials on screen, '
                    f'real business results displayed, trust and credibility visuals, {s}'
                ),
                'voiceover_long': (
                    f'Over ten thousand businesses across the UK and US already trust our platform. '
                    f'From early-stage startups to established enterprises, '
                    f'we have helped teams of every size take back their time and accelerate their growth. '
                    f'Our customers rate us five stars for ease of use, reliability, and the speed '
                    f'at which they see real results — often within the first week.'
                ),
                'voiceover_short': 'Over ten thousand businesses trust our platform to drive their growth.',
            },
            {
                'visual_prompt': (
                    f'hands-on product demo, smooth interface walkthrough, '
                    f'clean animated UI, step-by-step setup process, {s}, professional screencast style'
                ),
                'voiceover_long': (
                    f'Getting started takes less than ten minutes. '
                    f'Connect your existing tools, set your preferences, and the platform does the rest. '
                    f'No technical knowledge required. No complex setup. No long onboarding. '
                    f'Our team is available around the clock to ensure your experience '
                    f'is smooth from day one — and every day after.'
                ),
                'voiceover_short': 'Getting started takes less than ten minutes. No technical knowledge required.',
            },
            {
                'visual_prompt': (
                    f'pricing and value proposition display, clean infographic, '
                    f'ROI calculator visual, cost savings highlighted, {s}, professional design'
                ),
                'voiceover_long': (
                    f'The return on investment is immediate. '
                    f'Most businesses recover the full cost of the platform in the first month alone '
                    f'simply from the hours saved. '
                    f'Flexible pricing means you only pay for what you use, '
                    f'and you can scale up or down at any time. '
                    f'There are no long-term contracts and no hidden fees — just results.'
                ),
                'voiceover_short': 'Most businesses recover the full cost in the very first month.',
            },
            {
                'visual_prompt': (
                    f'future of work visual, AI and humans collaborating, '
                    f'bright optimistic office environment, innovation theme, {s}, inspirational'
                ),
                'voiceover_long': (
                    f'The future of work is not about replacing people with machines. '
                    f'It is about giving your people the tools to do their best work. '
                    f'When your team is freed from repetitive tasks, they become more creative, '
                    f'more strategic, and more engaged. '
                    f'That is the real transformation — not just in efficiency, but in culture.'
                ),
                'voiceover_short': 'The future of work is about giving your people the tools to do their best.',
            },
            {
                'visual_prompt': (
                    f'award-winning company recognition, industry leader visuals, '
                    f'certifications and partnerships displayed, {s}, professional credibility design'
                ),
                'voiceover_long': (
                    f'Recognised as a leader in AI automation by industry analysts. '
                    f'Awarded best SaaS platform of the year two years running. '
                    f'Trusted by companies listed in the FTSE 100 and Fortune 500. '
                    f'Our platform meets the highest standards of security and compliance, '
                    f'so your data is always protected and your operations always reliable.'
                ),
                'voiceover_short': 'Recognised as the leading AI automation platform by industry analysts.',
            },
            {
                'visual_prompt': (
                    f'urgency and limited offer visual, countdown timer, '
                    f'exclusive deal display, professional marketing design, {s}'
                ),
                'voiceover_long': (
                    f'Right now, we are offering new customers an extended free trial — '
                    f'thirty days, full access, no credit card required. '
                    f'This is your opportunity to experience everything the platform can do '
                    f'before committing to a single penny. '
                    f'Thousands of businesses started exactly this way. '
                    f'The question is: are you ready to join them?'
                ),
                'voiceover_short': 'Get thirty days of full access free. No credit card required.',
            },
            {
                'visual_prompt': (
                    f'bold call to action screen, website URL prominent, '
                    f'modern typography, clean brand colors, {s}, professional closing visual'
                ),
                'voiceover_long': (
                    f'The time to act is now. '
                    f'Every day you wait is another day of manual work, missed opportunities, '
                    f'and your competitors pulling further ahead. '
                    f'Visit our website, start your free trial, and see the difference within your first week. '
                    f'Your business deserves better. '
                    f'And better starts today.'
                ),
                'voiceover_short': 'Start your free trial today and see the difference within your first week.',
            },
        ],

        'educational': [
            {
                'visual_prompt': (
                    f'bright modern learning environment, clean desk with laptop and notebook, '
                    f'inspiring educational atmosphere, {s}, professional photography, 8k'
                ),
                'voiceover_long': (
                    f'Welcome. Today we are going to break down everything you need to know about {subject}. '
                    f'Whether you are completely new to this topic or looking to deepen your understanding, '
                    f'this is designed to be the clearest, most practical explanation you have ever seen. '
                    f'No jargon. No fluff. Just the real information, explained simply.'
                ),
                'voiceover_short': f'Today we break down everything you need to know about {subject}.',
            },
            {
                'visual_prompt': (
                    f'common misconception displayed visually, myth-busting graphic, '
                    f'confused expression, question marks, {s}, educational design'
                ),
                'voiceover_long': (
                    f'Most people approach this topic completely wrong. '
                    f'They have been taught outdated methods, given incorrect information, '
                    f'or simply never had anyone explain the fundamentals clearly. '
                    f'That is not their fault — most explanations out there are either too technical, '
                    f'too vague, or designed to confuse rather than clarify. '
                    f'We are going to fix that right now.'
                ),
                'voiceover_short': 'Most people approach this completely wrong — here is why.',
            },
            {
                'visual_prompt': (
                    f'step one of process shown clearly, numbered diagram, '
                    f'clean visual explanation, educational infographic, {s}'
                ),
                'voiceover_long': (
                    f'Step one. This is where most beginners get stuck, '
                    f'and it is the most important foundation you can build. '
                    f'Before anything else, you need to understand the core principle behind this entire topic. '
                    f'Once you have this locked in, everything else becomes significantly easier to understand. '
                    f'Take your time here. This step rewards patience.'
                ),
                'voiceover_short': 'Step one is the foundation everything else is built on.',
            },
            {
                'visual_prompt': (
                    f'step two visual demonstration, practical example shown, '
                    f'hands-on learning visual, {s}, clear educational design'
                ),
                'voiceover_long': (
                    f'Step two builds directly on what you just learned. '
                    f'Now we take the core principle and apply it to a real scenario. '
                    f'This is where theory becomes practice, and practice becomes skill. '
                    f'The most important thing to understand at this stage is the relationship '
                    f'between input and output — what you put in directly determines what you get out.'
                ),
                'voiceover_short': 'Step two is where theory becomes practice.',
            },
            {
                'visual_prompt': (
                    f'common mistakes and pitfalls visual, warning signs, '
                    f'avoid these errors graphic, {s}, educational warning design'
                ),
                'voiceover_long': (
                    f'Before we move on, let us talk about the three most common mistakes people make. '
                    f'First, rushing through the foundation before it is solid. '
                    f'Second, trying to apply advanced techniques before mastering the basics. '
                    f'Third, ignoring the feedback and data that tells you what is and is not working. '
                    f'Avoiding these three mistakes alone will put you ahead of ninety percent of beginners.'
                ),
                'voiceover_short': 'These three mistakes are holding most beginners back.',
            },
            {
                'visual_prompt': (
                    f'advanced techniques displayed, expert level visual, '
                    f'next level skills graphic, {s}, professional educational design'
                ),
                'voiceover_long': (
                    f'Once you have the basics solid, these are the advanced techniques that separate '
                    f'good practitioners from exceptional ones. '
                    f'These are not secrets — they are simply the next logical steps that most guides '
                    f'never cover because they assume you will figure them out on your own. '
                    f'We are not going to make that assumption. Let us go through them together.'
                ),
                'voiceover_short': 'These advanced techniques separate good from exceptional.',
            },
            {
                'visual_prompt': (
                    f'real world application example, case study visual, '
                    f'practical results shown, {s}, professional case study design'
                ),
                'voiceover_long': (
                    f'Let us look at a real example. This case study shows exactly how someone '
                    f'applied these principles and the results they achieved. '
                    f'Notice how each step builds on the previous one, '
                    f'and how the results compound over time. '
                    f'This is not a cherry-picked success story — '
                    f'this is the typical outcome when the process is followed correctly.'
                ),
                'voiceover_short': 'Here is a real example of these principles in action.',
            },
            {
                'visual_prompt': (
                    f'tools and resources recommendation visual, '
                    f'curated toolkit display, resource guide graphic, {s}'
                ),
                'voiceover_long': (
                    f'These are the tools and resources I recommend. '
                    f'I have tested dozens of options and these consistently deliver the best results '
                    f'for people at every level, from complete beginners to experienced practitioners. '
                    f'You do not need all of them — start with the first two and add the others '
                    f'as your skills develop. Complexity is the enemy of progress at the beginning.'
                ),
                'voiceover_short': 'These are the tools that consistently deliver the best results.',
            },
            {
                'visual_prompt': (
                    f'progress milestones and timeline, achievement roadmap visual, '
                    f'learning journey graphic, {s}, motivational design'
                ),
                'voiceover_long': (
                    f'Here is the realistic timeline you should expect. '
                    f'In the first week, you will feel overwhelmed — that is completely normal and expected. '
                    f'By the end of the first month, the core concepts will feel natural. '
                    f'By month three, you will be applying them confidently in real situations. '
                    f'The learning curve is real, but it is manageable when you know what to expect.'
                ),
                'voiceover_short': 'Here is the realistic timeline you should expect on this journey.',
            },
            {
                'visual_prompt': (
                    f'community and support visual, people learning together, '
                    f'online community platform, {s}, warm educational atmosphere'
                ),
                'voiceover_long': (
                    f'You do not have to do this alone. '
                    f'Our community of learners is one of the most active and supportive '
                    f'you will find anywhere. Ask questions, share your progress, get feedback, '
                    f'and learn from people who are a few steps ahead of where you are right now. '
                    f'The fastest way to learn is to surround yourself with others on the same path.'
                ),
                'voiceover_short': 'Join a community of learners supporting each other every step of the way.',
            },
            {
                'visual_prompt': (
                    f'final summary and key takeaways visual, '
                    f'numbered list of main points, clean educational summary, {s}'
                ),
                'voiceover_long': (
                    f'Let us bring it all together. The three things to remember: '
                    f'one, start with the foundation before anything else. '
                    f'Two, practice consistently — even fifteen minutes a day compounds dramatically. '
                    f'Three, track your progress and adjust based on real results, not assumptions. '
                    f'That is the entire framework. Everything else is just detail.'
                ),
                'voiceover_short': 'Three things to remember: foundation, consistency, and tracking.',
            },
            {
                'visual_prompt': (
                    f'call to subscribe and engage, channel branding visual, '
                    f'next video preview, {s}, YouTube optimised design'
                ),
                'voiceover_long': (
                    f'If this was helpful, subscribe — we publish new lessons every week, '
                    f'each one designed to be the clearest explanation of that topic available anywhere. '
                    f'Drop a comment below with your biggest question or challenge right now, '
                    f'and I will make sure we cover it in a future video. '
                    f'Thank you for watching. See you in the next one.'
                ),
                'voiceover_short': 'Subscribe for new lessons every week. See you in the next one.',
            },
        ],

        'social': [
            {
                'visual_prompt': (
                    f'ultra attention-grabbing opener visual, bold saturated colours, '
                    f'dynamic asymmetric composition, pattern interrupt design, {s}, social media viral'
                ),
                'voiceover_long': (
                    f'Stop scrolling. What I am about to show you changed everything for me, '
                    f'and once you see it, you will not be able to unsee it. '
                    f'This is not clickbait. This is not an exaggeration. '
                    f'This is something almost nobody is talking about, '
                    f'and the people who already know it have a serious advantage over everyone else.'
                ),
                'voiceover_short': 'Stop scrolling. What I am about to show you will change everything.',
            },
            {
                'visual_prompt': (
                    f'shocking statistic or fact displayed boldly, '
                    f'data visualisation with impact, viral hook graphic, {s}'
                ),
                'voiceover_long': (
                    f'Here is the fact that nobody wants you to know about {subject}. '
                    f'Ninety-two percent of people who try this fail in the first thirty days — '
                    f'not because it is hard, but because they are missing one critical piece of information '
                    f'that the top performers have figured out. '
                    f'That information is exactly what I am going to give you right now.'
                ),
                'voiceover_short': f'Ninety-two percent of people get {subject} completely wrong.',
            },
            {
                'visual_prompt': (
                    f'before and after transformation, dramatic visual contrast, '
                    f'split screen comparison, high impact social media style, {s}'
                ),
                'voiceover_long': (
                    f'Six months ago, I was exactly where you are right now. '
                    f'Trying everything. Seeing nothing work. Ready to give up entirely. '
                    f'Then I discovered this one approach, and everything shifted. '
                    f'Within thirty days I had completely transformed my results. '
                    f'The difference was not effort. It was not talent. It was this single insight.'
                ),
                'voiceover_short': 'Six months ago I was ready to give up. Then I discovered this.',
            },
            {
                'visual_prompt': (
                    f'secret or insider knowledge reveal, dramatic unveil visual, '
                    f'exclusive information graphic, {s}, viral revelation design'
                ),
                'voiceover_long': (
                    f'Here is the insight that changed everything. '
                    f'Most people are optimising for the wrong thing entirely. '
                    f'They are focused on the output when they should be focused on the system. '
                    f'Once you shift your focus from results to process, '
                    f'the results start happening automatically — '
                    f'and they happen faster and more consistently than anything you have tried before.'
                ),
                'voiceover_short': 'The secret is focusing on the system, not the result.',
            },
            {
                'visual_prompt': (
                    f'social proof montage, comments and reactions displayed, '
                    f'viral engagement metrics, testimonials scrolling, {s}'
                ),
                'voiceover_long': (
                    f'And I am not the only one this has worked for. '
                    f'Over the past six months, I have shared this with my community, '
                    f'and the results people are getting are genuinely remarkable. '
                    f'People who had struggled for years started seeing results within weeks. '
                    f'Not because they worked harder — because they finally had the right framework.'
                ),
                'voiceover_short': 'Thousands of people in my community have already used this.',
            },
            {
                'visual_prompt': (
                    f'step by step breakdown visual, numbered process, '
                    f'simple clear instructions, action-oriented design, {s}'
                ),
                'voiceover_long': (
                    f'Here is exactly what to do. Step one: identify the specific problem you are solving. '
                    f'Not the general category — the specific, measurable problem. '
                    f'Step two: apply the framework I just described to that specific problem only. '
                    f'Step three: measure the result after exactly seven days. '
                    f'Do not adjust anything before seven days. The data will tell you exactly what to do next.'
                ),
                'voiceover_short': 'Here is exactly what to do in three simple steps.',
            },
            {
                'visual_prompt': (
                    f'objection busting visual, common doubts addressed, '
                    f'FAQ style graphic, confidence-building design, {s}'
                ),
                'voiceover_long': (
                    f'I know what you are thinking. You have heard things like this before '
                    f'and they never worked. Fair enough. '
                    f'But ask yourself honestly — did you really apply the process fully? '
                    f'Or did you try it halfway, for three days, with one foot out the door? '
                    f'The framework only works when you commit to it completely. '
                    f'Half-effort gives you half-results, or more often, no results at all.'
                ),
                'voiceover_short': 'I know what you are thinking — here is the honest answer.',
            },
            {
                'visual_prompt': (
                    f'results and proof displayed, metrics and numbers, '
                    f'credibility evidence visual, {s}, data-driven social content'
                ),
                'voiceover_long': (
                    f'The numbers do not lie. '
                    f'In the last ninety days, this approach has produced these results consistently '
                    f'across completely different people with completely different starting points. '
                    f'The common thread is not background, resources, or experience — '
                    f'it is the willingness to follow the process exactly as described, '
                    f'even when it feels uncomfortable or counterintuitive.'
                ),
                'voiceover_short': 'The numbers speak for themselves — here is the proof.',
            },
            {
                'visual_prompt': (
                    f'urgency and FOMO visual, limited time graphic, '
                    f'now-or-never energy, {s}, high-conversion social design'
                ),
                'voiceover_long': (
                    f'Here is the thing about timing. '
                    f'The window for this specific approach being underutilised is closing. '
                    f'As more people discover it, the competitive advantage shrinks. '
                    f'The people who act now, who start applying this today, '
                    f'will have built a meaningful lead before it becomes mainstream. '
                    f'That window is open right now. The question is whether you will use it.'
                ),
                'voiceover_short': 'The window of opportunity here is closing. Act now.',
            },
            {
                'visual_prompt': (
                    f'engagement call to action, follow and share prompt, '
                    f'comment section reference, community building visual, {s}'
                ),
                'voiceover_long': (
                    f'If this landed for you, share it with one person who needs to hear it. '
                    f'Not because it helps me — because sharing information that works is '
                    f'one of the most genuinely useful things you can do for someone. '
                    f'Drop a comment with your biggest takeaway. '
                    f'I read every single one and I respond to as many as I can. '
                    f'Let me know what you are working on and I will point you in the right direction.'
                ),
                'voiceover_short': 'Share this with someone who needs it. Drop a comment below.',
            },
            {
                'visual_prompt': (
                    f'follow for more content visual, channel preview, '
                    f'what is coming next teaser, {s}, creator brand design'
                ),
                'voiceover_long': (
                    f'Follow for more content exactly like this — practical, no-fluff information '
                    f'that you can actually apply the same day you watch it. '
                    f'No motivation speeches. No vague advice. '
                    f'Just the specific, actionable insight that moves the needle. '
                    f'New content every week. Turn on notifications so you do not miss it. '
                    f'See you in the next one.'
                ),
                'voiceover_short': 'Follow for more. New content every week. See you in the next one.',
            },
        ],
    }

    # Select scenes: pick evenly-spaced scenes from template to hit num_scenes
    all_scenes = scene_templates[template_key]
    if num_scenes >= len(all_scenes):
        selected = all_scenes
    else:
        # Evenly sample scenes across the template list
        step = len(all_scenes) / num_scenes
        selected = [all_scenes[int(i * step)] for i in range(num_scenes)]

    # Build output: choose short or long voiceover based on target word count
    result = []
    for scene_data in selected:
        long_words = len(scene_data['voiceover_long'].split())
        short_words = len(scene_data['voiceover_short'].split())

        # Pick whichever voiceover is closest to target without going over
        if target_words >= long_words:
            voiceover = scene_data['voiceover_long']
        elif target_words >= short_words:
            voiceover = scene_data['voiceover_short']
        else:
            # Truncate short voiceover to word count
            words = scene_data['voiceover_short'].split()[:max(5, target_words)]
            voiceover = ' '.join(words) + '.'

        result.append({
            'visual_prompt': scene_data['visual_prompt'],
            'voiceover': voiceover,
            'duration_sec': per_scene_sec,
        })

    return result


if __name__ == '__main__':
    import json
    import sys

    prompt = 'Create a UK SaaS marketing reel about AI automation'
    duration_min = 2.0

    if len(sys.argv) >= 2:
        prompt = sys.argv[1]
    if len(sys.argv) >= 3:
        duration_min = float(sys.argv[2])

    target_sec = duration_min * 60
    scenes = generate_script(prompt, target_duration_sec=target_sec)

    print(json.dumps(scenes, indent=2))
    print(f"\nScenes: {len(scenes)}")
    print(f"Per scene: {scenes[0]['duration_sec']:.1f}s")
    print(f"Total duration: {sum(s['duration_sec'] for s in scenes):.0f}s ({duration_min} min)")
    print(f"Voiceover words (scene 1): {len(scenes[0]['voiceover'].split())}")
