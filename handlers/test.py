from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.qviz import check_and_stop_dialog

test_questions = [
    {
        "question": "Как зовут Генерального директора Latoken?",
        "options": ["Виталик Бутерин", "Валентин Преображенский", "Павел Дуров"],
        "correct": 1,
        "explanation": "Генеральный директор Latoken - Валентин Преображенский"
    },
    {
        "question": "Во сколько будет проходить Объявление победителей, интервью и офферы?",
        "options": ["17:00", "18:00", "19:00"],
        "correct": 2,
        "explanation": "Объявление победителей, интервью и офферы состоятся в 19:00"
    },
    {
        "question": "Какие технологические направления будут рассматриваться на хакатоне?",
        "options": [
            "NFT, GameFi, Web3 Gaming",
            "Q learning, Layer 3, RAG, мультиагенты",
            "Метавселенные, Social-Fi, Play-to-Earn"
        ],
        "correct": 1,
        "explanation": "На хакатоне рассматриваются: Квантовый и распределенный AGI, Переход от Web 2 к Web 3, DeFi, Q learning, Layer 3, мультиагенты, RWA, мультимодальность, Re-Staking, RAG, zk Rollups, трансформеры, синтетика"
    }
]


async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await check_and_stop_dialog(update, context)

    context.user_data['current_question'] = 0
    context.user_data['correct_answers'] = 0
    context.user_data['answers'] = []

    question = test_questions[0]

    keyboard = [[InlineKeyboardButton(opt, callback_data=f"test_{i}")]
                for i, opt in enumerate(question['options'])]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🎯 Тестирование начинается!\nВопрос 1 из 3:\n\n{question['question']}",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("test_"):
        return

    current_q = context.user_data.get('current_question', 0)
    selected = int(query.data.split("_")[1])

    # Сохраняем ответ
    is_correct = selected == test_questions[current_q]['correct']
    context.user_data['answers'].append({
        'question': current_q,
        'selected': selected,
        'correct': is_correct
    })

    if is_correct:
        context.user_data['correct_answers'] = context.user_data.get('correct_answers', 0) + 1
        response = "✅ Правильно!"
    else:
        response = "❌ Неправильно!"

    current_q += 1
    context.user_data['current_question'] = current_q

    if current_q < len(test_questions):
        question = test_questions[current_q]
        keyboard = [[InlineKeyboardButton(opt, callback_data=f"test_{i}")]
                    for i, opt in enumerate(question['options'])]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.reply_text(
            f"{response}\n\nВопрос {current_q + 1} из 3:\n\n{question['question']}",
            reply_markup=reply_markup
        )
    else:
        # Формируем итоговое сообщение
        correct_count = context.user_data['correct_answers']
        result_message = f"{response}\n\n📊 Тестирование завершено!\n"
        result_message += f"Правильных ответов: {correct_count} из {len(test_questions)}\n\n"
        result_message += "📝 Разбор ответов:\n\n"

        for i, q in enumerate(test_questions):
            answer = context.user_data['answers'][i]
            result_message += f"Вопрос {i + 1}: "
            result_message += "✅" if answer['correct'] else "❌"
            result_message += f"\n{q['explanation']}"

            # Добавляем ответ пользователя если он неверный
            if not answer['correct']:
                user_answer = q['options'][answer['selected']]
                result_message += f"\nВаш ответ: {user_answer}"

            result_message += "\n\n"

        result_message += "🚀 Желаю удачи на хакатоне! Пусть ваши идеи и решения будут инновационными и успешными!"

        await query.message.reply_text(result_message)
