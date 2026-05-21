const fs = require('fs');
const path = require('path');

const { plugin } = require('selenium-with-fingerprints');

let fingerprint;

// Создание профиля
async function createProfile(profilePath) {
    console.log('Create profile');

    fs.mkdirSync(profilePath, { recursive: true });

    const fingerprintPath = `${profilePath}_info\\fingerprint.json`;

    if (fs.existsSync(fingerprintPath)) {
        console.log('Load fingerprint');

        fingerprint = fs.readFileSync(fingerprintPath, 'utf8');

    } else {
        console.log('Fetch fingerprint');

        fingerprint = await plugin.fetch('', {
            tags: ['Microsoft Windows', 'Chrome']
        });

        fs.mkdirSync(`${profilePath}_info`, { recursive: true });

        fs.writeFileSync(fingerprintPath, fingerprint);
    }
}

// Открытие профиля
async function open(profilePath) {
    console.log('Open profile');

    const fingerprintPath = `${profilePath}_info\\fingerprint.json`;

    fingerprint = fs.readFileSync(fingerprintPath, 'utf8');

    plugin.useFingerprint(fingerprint);

    plugin.useProfile(path.resolve(profilePath), {});

    if (process.argv[4] !== 'None') {
        console.log('Use proxy:', process.argv[4]);

        plugin.useProxy(process.argv[4], {
            changeTimezone: true,
            changeGeolocation: true,
        });
    }

    console.log('Starting browser');

    const browser = await plugin.spawn({
        headless: false
    });

    console.log(JSON.stringify({
        port: browser.port
    }));

    setInterval(() => {}, 1000);
}

// Главная функция
async function manageProfile(profilePath) {

    if (!fs.existsSync(profilePath)) {
        await createProfile(profilePath);
    }

    await open(profilePath);
}

const profilePath = `${process.argv[2]}\\${process.argv[3]}`;

manageProfile(profilePath).catch(console.error);

// node .\driver.js "E:\\Universal-Driver\\Drivers\\profiles" "Profile_node_1" "None" 