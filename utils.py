async def execute_slash_command(self, channel, command, options=None, delay=None):
        """Execute a slash command and wait for response"""
        if delay is None:
            delay = float(self.bot.config['DEFAULT_DELAY'])

        try:
            # Log command execution
            self.logger.info(f"Executing command: {command} with options: {options}")

            # Format the command exactly as needed for the target bot
            if command == "remove-money":
                # Special formatting for remove-money command without using target: prefix
                cmd = f"!remove-money {options['target']} {options['amount']}"
            else:
                # Standard slash command formatting
                cmd = f"!" + command # Changed prefix to ! for Unbelievaboat
                if options:
                    option_parts = []
                    for k, v in options.items():
                        option_parts.append(f"{k}:{v}")
                    cmd += " " + " ".join(option_parts)

            # Add detailed debug logging for the final command
            self.logger.info(f"Sending formatted command to channel: {cmd}")

            # Send the command
            await channel.send(cmd)

            # Wait for the specified delay
            await asyncio.sleep(delay)

            # Log successful execution
            self.logger.info(f"Command {command} executed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to execute command {command}: {str(e)}")
            return False
