// Importing required modules
const fs = require('fs');
const path = require('path');

const { json } = require('express');
const { Builder } = require('selenium-webdriver');
const { Options } = require('selenium-webdriver/chrome');
const { plugin } = require('selenium-with-fingerprints');
// npm install express selenium-webdriver selenium-with-fingerprints

// Variables for browser instance and fingerprint
let browser;
let fingerprint;

// Function to create a new browser profile or load an existing one
async function createProfile(profilePath) {
    console.log('Creat new browser profile '+profilePath)
    // Setting up Chrome options with user data directory and headless mode

    console.log('Setting path profile')
    const options = new Options()
    .addArguments(`--user-data-dir=${path.resolve(profilePath)}`)
    .addArguments("--lang=en-US")
    .addArguments("--accept-lang=en-US,en")

    // Checking if fingerprint file exists and if forced fingerprint regeneration is requested
    if (fs.existsSync(`${profilePath}_info\\fingerprint.json`)) {
        console.log('Reading fingerprint from file')
        fingerprint = fs.readFileSync(`${profilePath}_info\\fingerprint.json`, 'utf8');
    } else {
        console.log('Get new fingerprint')
        fingerprint = await plugin.fetch('', { tags: ['Microsoft Windows', 'Chrome'], });

        console.log('Saving fingerprint to file: '+profilePath)
        fs.writeFileSync(`${profilePath}_info\\fingerprint.json`, fingerprint, (err) => {
            if (err) throw err;
            console.log('Fingerprint saved');
        });
    }

    console.log('Add fingerprint')
    plugin.useFingerprint(fingerprint);

    const timeout = setTimeout(async () => {
        console.warn('⏱ Время ожидания истекло. Принудительное завершение.');
        timedOut = true;

        // Принудительно убиваем процесс, если завис
        if (browser) {
            try {
                await browser.quit(); // попытаемся закрыть
            } catch (e) {}
        }

        console.log(JSON.stringify({ status: 'timeout forced quit' }));
        process.exit(0); // форс-выход
    }, 30000); // 10 секунд

    try {
        browser = await plugin.launch(new Builder().setChromeOptions(options));
        if (!timedOut) {
            clearTimeout(timeout);

            console.log('Закрытие браузера');
            await browser.quit();

            console.log(JSON.stringify({ status: 'ok' }));
        }
    } catch (err) {
        clearTimeout(timeout);
        console.error('Ошибка при запуске браузера:', err);
    }
}

// Function to open an existing browser profile
async function open(profilePath) {
    console.log('Open profile')

    console.log('Add path profile')
    plugin.useProfile(path.resolve(profilePath), {});
    
    // Checking if a proxy is provided
    if (process.argv[4] != 'None') {
        // Configuring browser to use proxy
        console.log('Add proxy ro profile: '+ process.argv[4])
        plugin.useProxy(process.argv[4], {
            // Change browser timezone according to proxy:
            changeTimezone: true,
            // Replace browser geolocation according to proxy:
            changeGeolocation: true,
        });
    }

    console.log('Starting browser')
    browser = await plugin.spawn({ headless: false });

    // Logging port information
    console.log(JSON.stringify({
        'port': browser.port
    }));
}

// Main function to manage browser profiles
async function manageProfile(profilePath) {
    console.log(profilePath)
    if (fs.existsSync(profilePath)) {
        // If profile exists, open it
        await open(profilePath);
    } else {
        // If profile doesn't exist, create it
        await createProfile(profilePath);
    }
}

console.log(process.argv[2], process.argv[3], process.argv[4])
// Constructing the profile path
const profilePath = `${process.argv[2]}\\${process.argv[3]}`;
// Managing the profile
manageProfile(profilePath);

// "C:\\Users\\dgana\\Desktop\\FacebookFarm\\Facebook\\Drivers\\profiles" profile1 195.42.232.39:13917:ak8yHu:aT6FekAM5PYA
// npm install express
// npm install selenium
// npm install selenium-with-fingerprints'