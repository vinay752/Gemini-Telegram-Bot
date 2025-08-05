from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode
from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
from dotenv import load_dotenv
import os
from io import BytesIO

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Ensure keys are set
if not BOT_TOKEN or not GEMINI_API_KEY:
    raise ValueError("BOT_TOKEN or GEMINI_API_KEY is missing in .env")

# Setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
client = genai.Client(api_key=GEMINI_API_KEY)
google_search_tool = Tool(google_search=GoogleSearch())

# Handlers
async def gemini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = ' '.join(context.args)
    if not question:
        await update.message.reply_text("Usage: /gemini What is AI?")
    else:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[f"Generate answer in minimum token and maximum of 70 tokens: {question}"],
            config=GenerateContentConfig(
                tools=[google_search_tool],
                max_output_tokens=100,
                temperature=0.1
            )
        ).text
        await update.message.reply_text(response.text if hasattr(response, 'text') else "❌ Failed to generate answer.")

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = ' '.join(context.args)
    if '|' not in question or len(question.split("|")) != 2:
        await update.message.reply_text("Usage: /translate Telugu | How are you?")
        return

    languages, text = [x.strip() for x in question.split("|")]
    for language in languages.split(","):
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[f"{language} | {text}"],
            config=GenerateContentConfig(
                tools=[google_search_tool],
                max_output_tokens=100,
                temperature=0.1
            )
        )
        await update.message.reply_text(f"{language.capitalize()}: {response.text}")

async def imagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contents = ' '.join(context.args)
    if not contents:
        await update.message.reply_text("Usage: /imagen Create an image of an orange cat in a cricket stadium")
        return

    await update.message.reply_text("Generating image... please wait 🧠🖼️")

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=contents,
        config=GenerateContentConfig(response_modalities=['Text', 'Image'])
    )

    for part in response.candidates[0].content.parts:
        if part.text:
            await update.message.reply_text(part.text)
        elif part.inline_data:
            image_bytes = BytesIO(part.inline_data.data)
            image_bytes.seek(0)
            await update.message.reply_photo(photo=image_bytes)



# Add handlers
app.add_handler(CommandHandler("gemini", gemini))
app.add_handler(CommandHandler("translate", translate))
app.add_handler(CommandHandler("imgen", imagen))

# Run bot
app.run_polling()
