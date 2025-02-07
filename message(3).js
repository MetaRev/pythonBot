// bot.js

const { Client, GatewayIntentBits, Partials, EmbedBuilder, SlashCommandBuilder, REST, Routes } = require('discord.js');

// Create a new client instance with the required intents
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent, // Allow the bot to access message content
        GatewayIntentBits.DirectMessages, // Allow bot to read and send DMs
        GatewayIntentBits.GuildMembers, // Listen for member join events
    ],
    partials: [Partials.Channel], // Allow partial channels for DMs
});

// Your Discord User ID (only you can use certain commands)
const allowedUserId = '855039931294547979'; // Replace with your Discord User ID
const welcomeChannelId = '1332869292592463982'; // Replace with your channel ID for welcome messages
const defaultRoleId = '1253307152823615528'; // Replace with the ID of the role to assign to new members
const token = ''; // Replace with your bot token

// Unacceptable texts list
const unacceptableTexts = ['ass', 'bitch', 'dick', 'fuck', 'nigga', 'niga', 'nigger', 'niger', 'shit', 'whore', 'wtf']; // Add any unacceptable words or phrases here

// User warning tracking (this could be saved to a database, but for now, it's in memory)
const userWarnings = {};

// Slash command setup
const rest = new REST({ version: '10' }).setToken(token);

    // Check if the message starts with the "!say" command
    if (message.content.startsWith('!say')) 
        // Extract the text after "!say"
        const textToSay = message.content.slice(5).trim();

        // Check if there's any text to respond with
        if (!textToSay) {
            await message.reply("Please provide a message after `!say`!");
            return;
        }
        
    new SlashCommandBuilder()
        .setName('mdelete')
        .setDescription('Delete a specific number of messages in the current channel.')
        .addIntegerOption(option =>
            option.setName('number').setDescription('Number of messages to delete (1-100)').setRequired(true)
        ),

// Register the commands
(async () => {
    try {
        console.log('Refreshing slash commands...');
        await rest.put(
            Routes.applicationCommands('1284577686563454976'), // Replace with your bot's Application ID
            { body: commands.map(command => command.toJSON()) }
        );
        console.log('Slash commands registered!');
    } catch (error) {
        console.error('Error registering commands:', error);
    }
})();

// When the bot is ready
client.once('ready', () => {
    console.log(`Logged in as ${client.user.tag}!`);
});

// Listen for slash command interactions
client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) return;

    const { commandName, user, channel } = interaction;

    if (commandName === 'say') {
        // /say command
        const message = interaction.options.getString('message');
        const targetChannel = interaction.options.getChannel('channel');
        
        // Check if the selected channel is a text channel
        if (targetChannel.type === 'GUILD_TEXT') {
            await targetChannel.send(message);
            await interaction.reply({ content: `Message sent to ${targetChannel.name}.`, ephemeral: true });
        } else {
            await interaction.reply({ content: 'You can only send messages to text channels.', ephemeral: true });
        }
    }

    if (commandName === 'mdelete') {
        // /mdelete command
        if (user.id !== allowedUserId) {
            await interaction.reply({ content: 'You are not authorized to use this command.', ephemeral: true });
            return;
        }

        const number = interaction.options.getInteger('number');
        if (number < 1 || number > 100) {
            await interaction.reply({ content: 'Please provide a number between 1 and 100.', ephemeral: true });
            return;
        }

        try {
            const messages = await channel.messages.fetch({ limit: number });
            await channel.bulkDelete(messages);
            await interaction.reply({ content: `Deleted ${number} messages.`, ephemeral: true });
        } catch (error) {
            console.error('Error deleting messages:', error);
            await interaction.reply({ content: 'I couldn’t delete the messages.', ephemeral: true });
        }
    }
});

// Listen for messages in Discord (for guild and DM messages)
client.on('messageCreate', async (message) => {
    // Ignore messages from bots (including the bot itself)
    if (message.author.bot) return;

    // Check if the message is "help"
    if (message.content.toLowerCase().includes("help")) {
        message.reply(`This feature is coming in the future, stay tuned! ${message.author}!`); // Bot replies and mentions the user
}

    // Check if the message is "info"
    if (message.content.toLowerCase().includes("!info")) {
        message.reply(`I'm ready to take command! - Kokusz Bot`); // Bot replies and mentions the user
    }

    // Check for unacceptable texts
    for (const badText of unacceptableTexts) {
        if (message.content.toLowerCase().includes(badText.toLowerCase())) {
            const userId = message.author.id;

            // Increment or initialize user's warning count
            if (!userWarnings[userId]) {
                userWarnings[userId] = 1;
            } else {
                userWarnings[userId]++;
            }

            // Delete the message
            await message.delete().catch(console.error);

            // Send a warning message in the channel
            message.channel.send(`${message.author.tag} wrote a bad message and has received warning #${userWarnings[userId]}.`);

            // Send DM to the user about the warning
            const user = await client.users.fetch(userId);
            if (user) {
                user.send(`Your message: "${message.content}" was flagged for containing unacceptable text. You now have ${userWarnings[userId]} warning(s).`);

                // Inform you (the owner) about the warning
                const owner = await client.users.fetch(allowedUserId);
                if (owner) {
                    owner.send(`${user.tag} has received warning #${userWarnings[userId]}. Message: "${message.content}"`);
                }
            }

            // Handle timeouts based on the warning count
            let timeoutDuration;
            if (userWarnings[userId] === 1) {
                timeoutDuration = 60 * 60 * 1000; // 1 hour timeout
            } else if (userWarnings[userId] === 2) {
                timeoutDuration = 3 * 60 * 60 * 1000; // 3 hours timeout
            } else if (userWarnings[userId] >= 3) {
                timeoutDuration = 6 * 60 * 60 * 1000; // 6 hours timeout
            }

            // Apply timeout if warning count is 1 or more
            if (timeoutDuration) {
                const member = await message.guild.members.fetch(userId).catch(console.error);
                if (member) {
                    member.timeout(timeoutDuration, `Received ${userWarnings[userId]} warning(s)`)
                        .then(() => {
                            message.channel.send(`${message.author.tag} has been timed out for ${timeoutDuration / 1000 / 60} minutes due to their warning count.`);
                        })
                        .catch(console.error);
                }
            }

            break; // Exit loop once bad text is found
        }
    }
});

// Listen for new members joining the server
client.on('guildMemberAdd', async (member) => {
    try {
        // Get the total member count
        const memberCount = member.guild.memberCount;

        // Send a welcome message in the designated welcome channel
        const welcomeChannel = member.guild.channels.cache.get(welcomeChannelId);
        if (welcomeChannel) {
            welcomeChannel.send(`Welcome to the server, ${member.user.tag}! We're now at ${memberCount} members!`);
        }

        // Add a role to the new member
        const role = member.guild.roles.cache.get(defaultRoleId);
        if (role) {
            await member.roles.add(role);
            console.log(`Assigned ${role.name} to ${member.user.tag}`);
        }
    } catch (error) {
        console.error('Error assigning role or sending welcome message:', error);
    }
});

// Login to Discord with your app's token
client.login(token);