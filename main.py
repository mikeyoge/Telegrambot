from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler
from telegram.ext.filters import Command

class DiceGame:
    def __init__(self):
        self.players = {}
        self.game_active = False
        self.current_round = 0
        self.turn_index = 0

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("Join Game", callback_data='join_game')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Welcome to the Dice Game! Click below to join.', reply_markup=reply_markup)

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user = query.from_user
        await query.answer()

        if query.data == 'join_game':
            if len(self.players) >= 2:
                await query.edit_message_text("The game is already full!")
                return
            if user.id not in self.players:
                self.players[user.id] = {'name': user.first_name, 'scores': []}
                await query.edit_message_text(f"{user.first_name} has joined the game.")
                if len(self.players) == 2:
                    self.game_active = True
                    self.current_round = 1
                    await context.bot.send_message(chat_id=query.message.chat_id,
                                                   text="Game is starting now! Each player will roll dice three times.")
                    await self.next_turn(context, query.message.chat_id)
            else:
                await query.edit_message_text("You are already registered in the game!")

    async def roll_dice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not self.game_active:
            await update.message.reply_text("Game has not started. Please wait for players to join.")
            return

        if user.id not in self.players:
            await update.message.reply_text("You are not part of the game.")
            return

        current_player_id = list(self.players.keys())[self.turn_index]
        if user.id != current_player_id:
            await update.message.reply_text("It's not your turn to roll the dice.")
            return

        dice_roll = await context.bot.send_dice(chat_id=update.effective_chat.id, emoji="🎲")
        dice_value = dice_roll.dice.value
        self.players[user.id]['scores'].append(dice_value)
        await update.message.reply_text(f"{user.first_name} rolled a {dice_value}!")
        await self.next_turn(context, update.effective_chat.id)

    async def next_turn(self, context, chat_id):
        if self.current_round <= 3:
            self.turn_index = (self.turn_index + 1) % len(self.players)
            if self.turn_index == 0:
                self.current_round += 1
            if self.current_round > 3:
                await self.end_game(context, chat_id)
                return
            next_player_id = list(self.players.keys())[self.turn_index]
            next_player_name = self.players[next_player_id]['name']
            await context.bot.send_message(chat_id=chat_id,
                                           text=f"{next_player_name}'s turn to roll. Round {self.current_round}/3")
        else:
            await self.end_game(context, chat_id)

    async def end_game(self, context, chat_id):
        self.game_active = False
        winner = None
        max_score = -1
        results = "Game ended. Here are the results:\n"
        for player_id, data in self.players.items():
            total_score = sum(data['scores'])
            results += f"{data['name']} scored: {total_score}\n"
            if total_score > max_score:
                max_score = total_score
                winner = data['name']
        results += f"The winner is {winner} with a score of {max_score}."
        await context.bot.send_message(chat_id=chat_id, text=results)
        self.players = {}
        self.current_round = 0
        self.turn_index = 0

def main():
    application = Application.builder().token('Your Telegram Bot Token').build()

    game = DiceGame()
    application.add_handler(CommandHandler('start', game.start))
    application.add_handler(CallbackQueryHandler(game.button))
    application.add_handler(CommandHandler('roll', game.roll_dice))

    application.run_polling()

if __name__ == '__main__':
    main()
