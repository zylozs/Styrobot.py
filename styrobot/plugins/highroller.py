from plugin import Plugin
import random
import logging
import styrobot

class HighRoller(Plugin):

    async def initialize(self, bot):
        self.callFlip = {}
        self.tag = 'highroller'
        self.shortTag = 'hr'

    @styrobot.plugincommand('Rolls a dice of size <number>', name='roll')
    async def _roll_(self, server, channel, author, number):
        """
        Rolls a dice of the size you provide. The number must be greater than 0.
        `!highroller roll <number>`
        **Example:** `!highroller roll 20`
        """
        if self.isNumber(number) and int(number) > 0:
            result = self.rollDice(int(number))

            self.logger.debug('[roll]: %s rolled a %s', author, str(result))
            await self.bot.send_message(channel, '<@' + author.id + '> rolled a ' + str(result))
        else:
            self.logger.debug('[roll]: You can\'t roll a dice smaller than 1.')
            await self.bot.send_message(channel, 'You can\'t roll a dice smaller than 1.')

    @styrobot.plugincommand('Call the next coinflip (Heads or Tails)', name='callflip')
    async def _callflip_(self, server, channel, author, name):
        """
        Call the next coinflip before it happens. Once two different people call it, the flip will automatically happen and the winner/s will be announced. You can call Heads or Tails. This command is not case sensitive.
        `!highroller callflip <name>`
        **Example call for heads:** `!highroller callflip Heads`
        **Example call for tails:** `!highroller callflip Tails`
        """
        firstWord = name.lower()

        if firstWord == 'head' or firstWord == 'heads':
            self.callFlip[str(author)] = ['heads', author.id]
        elif firstWord == 'tail' or firstWord == 'tails':
            self.callFlip[str(author)] = ['tails', author.id]
        else:
            await self.bot.send_message(channel, 'You have to specify heads or tails!')
            return

        if len(self.callFlip) == 2:
            p1name = ''
            p1call = ''
            p1id = ''
            message = ''
            logmessage = ''
            result = self.flipCoin().lower()
            for key, value in self.callFlip.items():
                if p1name == '' and p1call == '':
                    p1name = key
                    p1call = value[0]
                    p1id = value[1]
                else:
                    if result == p1call and result == value[0]:
                        message = 'It is a tie between <@' + p1id + '> and <@' + value[1] + '>!'
                        logmessage = 'It is a tie between ' + p1name + ' and ' + key + '!'
                    elif result == p1call and result != value[0]:
                        message = '<@' + p1id + '> wins the coin flip!'
                        logmessage = p1name + ' wins the coin flip!'
                    elif result == value[0] and result != p1call:
                        message = '<@' + value[1] + '> wins the coin flip!'
                        logmessage = key + ' wins the coin flip!'
                    else:
                        message = 'Nobody wins the coin flip!'

                    break

            self.callFlip = {}
            self.logger.debug('[callflip]: %s', logmessage)
            await self.bot.send_message(channel, message)

    @styrobot.plugincommand('Flips a coin', name='flipcoin')
    async def _flipcoin_(self, server, channel, author):
        """
        Flips a coin.
        `!highroller flipcoin`
        **Example:** `!highroller flipcoin`
        """
        result = self.flipCoin()
        self.logger.debug('[flipcoin]: %s!', result)
        await self.bot.send_message(channel, result + '!');

    def rollDice(self, num):
        return random.randint(1, num)

    def flipCoin(self):
        result = self.rollDice(2)

        if result == 1:
            return 'Heads'
        else:
            return 'Tails'

    def isNumber(self, num):
        try:
            int(num)
            return True
        except ValueError:
            return False
