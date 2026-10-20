// Shared by the hook script and the display mod. Edit freely; keep the shape.
export default [
  {
    "id": "curl-pipe-shell", "risk": "danger",
    "match": "\\b(curl|wget)\\b[^|\\n]*\\|\\s*(sudo\\s+)?(ba|z)?sh\\b",
    "text": {
      "english": "Downloads a script from the internet and runs it right away.",
      "urdu:roman": "Internet se script download ho kar foran chalegi.",
      "urdu:native": "انٹرنیٹ سے اسکرپٹ ڈاؤن لوڈ ہو کر فوراً چلے گی۔",
      "hindi:roman": "Internet se script download hokar turant chalegi.",
      "hindi:native": "इंटरनेट से स्क्रिप्ट डाउनलोड होकर तुरंत चलेगी।",
      "dutch": "Downloadt een script van internet en voert het meteen uit."
    }
  },
  {
    "id": "force-push", "risk": "danger",
    "match": "\\bgit\\s+push\\b[^\\n]*(\\s--force(-with-lease)?\\b|\\s-[a-zA-Z]*f\\b|\\s\\+\\S)",
    "text": {
      "english": "Overwrites the branch on GitHub with your local copy. Other people's commits on it can be lost.",
      "urdu:roman": "GitHub par branch ko aapki local copy se overwrite karega. Doosron ke commits gum ho sakte hain.",
      "urdu:native": "GitHub پر برانچ کو آپ کی لوکل کاپی سے اوور رائٹ کرے گا۔ دوسروں کے کمٹس ضائع ہو سکتے ہیں۔",
      "hindi:roman": "GitHub par branch ko aapki local copy se overwrite karega. Doosron ke commits kho sakte hain.",
      "hindi:native": "GitHub पर ब्रांच को आपकी लोकल कॉपी से ओवरराइट करेगा। दूसरों के कमिट खो सकते हैं।",
      "dutch": "Overschrijft de branch op GitHub met jouw lokale versie. Commits van anderen kunnen verloren gaan."
    }
  },
  {
    "id": "push-delete", "risk": "danger",
    "match": "\\bgit\\s+push\\b[^\\n]*(\\s--delete\\b|\\s-d\\b|\\s:\\S)",
    "text": {
      "english": "Deletes this branch on GitHub, for everyone on the team.",
      "urdu:roman": "Yeh branch GitHub par sab ke liye delete ho jayegi.",
      "urdu:native": "یہ برانچ GitHub پر سب کے لیے ڈیلیٹ ہو جائے گی۔",
      "hindi:roman": "Yeh branch GitHub par sab ke liye delete ho jayegi.",
      "hindi:native": "यह ब्रांच GitHub पर सबके लिए डिलीट हो जाएगी।",
      "dutch": "Verwijdert deze branch op GitHub, voor iedereen in het team."
    }
  },
  {
    "id": "branch-force-delete", "risk": "danger", "flags": "",
    "match": "\\bgit\\s+branch\\b[^\\n]*(\\s-[a-zA-Z]*D\\b|--delete\\s+--force|--force\\s+--delete)",
    "text": {
      "english": "Deletes this branch even if its work is not merged anywhere.",
      "urdu:roman": "Yeh branch delete hogi, chahe us ka kaam kahin merge na hua ho.",
      "urdu:native": "یہ برانچ ڈیلیٹ ہو گی، چاہے اس کا کام کہیں مرج نہ ہوا ہو۔",
      "hindi:roman": "Yeh branch delete hogi, chahe uska kaam kahin merge na hua ho.",
      "hindi:native": "यह ब्रांच डिलीट होगी, चाहे उसका काम कहीं मर्ज न हुआ हो।",
      "dutch": "Verwijdert deze branch, ook als het werk nergens gemerged is."
    }
  },
  {
    "id": "stash-delete", "risk": "danger",
    "match": "\\bgit\\s+stash\\s+(clear|drop)\\b",
    "text": {
      "english": "Deletes your stashed changes for good.",
      "urdu:roman": "Aapke stash kiye hue changes hamesha ke liye mit jayenge.",
      "urdu:native": "آپ کے سٹیش کیے ہوئے چینجز ہمیشہ کے لیے مٹ جائیں گے۔",
      "hindi:roman": "Aapke stash kiye hue changes hamesha ke liye mit jayenge.",
      "hindi:native": "आपके स्टैश किए हुए बदलाव हमेशा के लिए मिट जाएंगे।",
      "dutch": "Gooit je gestashte wijzigingen voorgoed weg."
    }
  },
  {
    "id": "reset-hard", "risk": "danger",
    "match": "\\bgit\\s+reset\\b[^\\n]*--hard",
    "text": {
      "english": "Throws away all changes that are not committed yet. They cannot be recovered.",
      "urdu:roman": "Files mein jo changes commit nahi hue, sab mit jayenge. Wapas nahi aayenge.",
      "urdu:native": "فائلوں میں جو چینجز کمٹ نہیں ہوئے، سب مٹ جائیں گے۔ واپس نہیں آئیں گے۔",
      "hindi:roman": "Files mein jo changes commit nahi hue, sab mit jayenge. Wapas nahi aayenge.",
      "hindi:native": "फ़ाइलों में जो बदलाव कमिट नहीं हुए, सब मिट जाएंगे। वापस नहीं आएंगे।",
      "dutch": "Gooit alle wijzigingen weg die nog niet gecommit zijn. Je krijgt ze niet terug."
    }
  },
  {
    "id": "git-clean", "risk": "danger",
    "match": "\\bgit\\s+clean\\b[^\\n]*\\s-[a-zA-Z]*f",
    "text": {
      "english": "Deletes new files that were never committed. They cannot be recovered.",
      "urdu:roman": "Nayi files jo kabhi commit nahi huin, delete ho jayengi. Wapas nahi aayengi.",
      "urdu:native": "نئی فائلیں جو کبھی کمٹ نہیں ہوئیں، ڈیلیٹ ہو جائیں گی۔ واپس نہیں آئیں گی۔",
      "hindi:roman": "Nayi files jo kabhi commit nahi huin, delete ho jayengi. Wapas nahi aayengi.",
      "hindi:native": "नई फ़ाइलें जो कभी कमिट नहीं हुईं, डिलीट हो जाएंगी। वापस नहीं आएंगी।",
      "dutch": "Verwijdert nieuwe bestanden die nooit gecommit zijn. Je krijgt ze niet terug."
    }
  },
  {
    "id": "discard-edits", "risk": "danger",
    "match": "\\bgit\\s+checkout\\s+--\\s|\\bgit\\s+checkout\\s+\\.(\\s|$)|\\bgit\\s+restore\\s+(?!--staged\\b)\\S",
    "text": {
      "english": "Throws away your edits that are not committed yet.",
      "urdu:roman": "Aapki jo edits commit nahi huin, woh mit jayengi.",
      "urdu:native": "آپ کی جو ایڈٹس کمٹ نہیں ہوئیں، وہ مٹ جائیں گی۔",
      "hindi:roman": "Aapke jo changes commit nahi hue, woh mit jayenge.",
      "hindi:native": "आपके जो बदलाव कमिट नहीं हुए, वो मिट जाएंगे।",
      "dutch": "Gooit je wijzigingen weg die nog niet gecommit zijn."
    }
  },
  {
    "id": "rm-recursive", "risk": "danger",
    "match": "(^|[;&|(]\\s*|\\s)(sudo\\s+)?(\\S*\\/)?\\\\?rm(\\s+-{1,2}[a-zA-Z][\\w-]*)*\\s+(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)\\b",
    "text": {
      "english": "Deletes these files or folders for good. There is no recycle bin.",
      "urdu:roman": "Yeh files ya folders hamesha ke liye delete honge. Recycle bin mein nahi jayenge.",
      "urdu:native": "یہ فائلیں یا فولڈر ہمیشہ کے لیے ڈیلیٹ ہوں گے۔",
      "hindi:roman": "Yeh files ya folders hamesha ke liye delete honge. Recycle bin mein nahi jayenge.",
      "hindi:native": "ये फ़ाइलें या फ़ोल्डर हमेशा के लिए डिलीट होंगे।",
      "dutch": "Verwijdert deze bestanden of mappen voorgoed. Er is geen prullenbak."
    }
  },
  {
    "id": "drop-data", "risk": "danger",
    "match": "\\b(drop\\s+(table|database|schema)|truncate\\s+table|delete\\s+from)\\b",
    "text": {
      "english": "Deletes data from the database for good.",
      "urdu:roman": "Database ka data hamesha ke liye delete hoga.",
      "urdu:native": "ڈیٹابیس کا ڈیٹا ہمیشہ کے لیے ڈیلیٹ ہو گا۔",
      "hindi:roman": "Database ka data hamesha ke liye delete hoga.",
      "hindi:native": "डेटाबेस का डेटा हमेशा के लिए डिलीट होगा।",
      "dutch": "Verwijdert data uit de database voorgoed."
    }
  },
  {
    "id": "infra-delete", "risk": "danger",
    "match": "\\bkubectl\\s+delete\\b|\\bterraform\\s+destroy\\b|\\bhelm\\s+(uninstall|delete)\\b",
    "text": {
      "english": "Deletes part of the live servers or infrastructure.",
      "urdu:roman": "Live server ya infrastructure ka ek part delete hoga.",
      "urdu:native": "لائیو سرور یا انفراسٹرکچر کا ایک حصہ ڈیلیٹ ہو گا۔",
      "hindi:roman": "Live server ya infrastructure ka ek part delete hoga.",
      "hindi:native": "लाइव सर्वर या इंफ्रास्ट्रक्चर का एक हिस्सा डिलीट होगा।",
      "dutch": "Verwijdert een deel van de live servers of infrastructuur."
    }
  },
  {
    "id": "docker-delete", "risk": "danger",
    "match": "\\bdocker\\s+(system\\s+prune|volume\\s+(rm|prune)|image\\s+prune|container\\s+prune|rm|rmi)\\b",
    "text": {
      "english": "Deletes Docker containers, images or data.",
      "urdu:roman": "Docker ke containers, images ya data delete honge.",
      "urdu:native": "Docker کے کنٹینرز، امیجز یا ڈیٹا ڈیلیٹ ہوں گے۔",
      "hindi:roman": "Docker ke containers, images ya data delete honge.",
      "hindi:native": "Docker के कंटेनर, इमेज या डेटा डिलीट होंगे।",
      "dutch": "Verwijdert Docker-containers, images of data."
    }
  },
  {
    "id": "publish", "risk": "danger",
    "match": "\\b(npm|yarn|pnpm)\\s+publish\\b|\\bcargo\\s+publish\\b|\\btwine\\s+upload\\b",
    "text": {
      "english": "Publishes a package publicly. A published version is hard to take back.",
      "urdu:roman": "Package public publish hoga. Publish hua version wapas lena mushkil hai.",
      "urdu:native": "پیکج پبلک پبلش ہو گا۔ پبلش ہوا ورژن واپس لینا مشکل ہے۔",
      "hindi:roman": "Package public publish hoga. Publish hua version wapas lena mushkil hai.",
      "hindi:native": "पैकेज पब्लिक पब्लिश होगा। पब्लिश हुआ वर्ज़न वापस लेना मुश्किल है।",
      "dutch": "Publiceert een package openbaar. Een gepubliceerde versie haal je niet makkelijk terug."
    }
  },
  {
    "id": "migrate", "risk": "caution",
    "match": "doctrine:migrations:migrate|artisan\\s+migrate|prisma\\s+migrate|db:migrate|alembic\\s+upgrade|manage\\.py\\s+migrate|flyway\\s+migrate",
    "text": {
      "english": "Changes the database structure. On a shared database, everyone is affected.",
      "urdu:roman": "Database ka structure badlega. Shared database ho to sab par asar hoga.",
      "urdu:native": "ڈیٹابیس کا اسٹرکچر بدلے گا۔ شیئرڈ ڈیٹابیس ہو تو سب پر اثر ہو گا۔",
      "hindi:roman": "Database ka structure badlega. Shared database ho to sab par asar hoga.",
      "hindi:native": "डेटाबेस का स्ट्रक्चर बदलेगा। शेयर्ड डेटाबेस हो तो सब पर असर होगा।",
      "dutch": "Verandert de structuur van de database. Bij een gedeelde database merkt iedereen dat."
    }
  },
  {
    "id": "rebase", "risk": "caution",
    "match": "\\bgit\\s+rebase\\b",
    "text": {
      "english": "Rewrites the commit history of this branch.",
      "urdu:roman": "Is branch ki commit history dobara likhi jayegi.",
      "urdu:native": "اس برانچ کی کمٹ ہسٹری دوبارہ لکھی جائے گی۔",
      "hindi:roman": "Is branch ki commit history dobara likhi jayegi.",
      "hindi:native": "इस ब्रांच की कमिट हिस्ट्री दोबारा लिखी जाएगी।",
      "dutch": "Schrijft de commitgeschiedenis van deze branch opnieuw."
    }
  },
  {
    "id": "permissions", "risk": "caution",
    "match": "\\b(chmod|chown)\\s+-R\\b",
    "text": {
      "english": "Changes the permissions of many files at once.",
      "urdu:roman": "Bohat saari files ki permissions ek saath badlengi.",
      "urdu:native": "بہت ساری فائلوں کی پرمیشنز ایک ساتھ بدلیں گی۔",
      "hindi:roman": "Bahut saari files ki permissions ek saath badlengi.",
      "hindi:native": "बहुत सारी फ़ाइलों की परमिशन एक साथ बदलेंगी।",
      "dutch": "Verandert de rechten van veel bestanden tegelijk."
    }
  },
  {
    "id": "push", "risk": "caution",
    "match": "\\bgit\\s+push\\b",
    "text": {
      "english": "Sends your commits to GitHub, where the team can see them.",
      "urdu:roman": "Aapke commits GitHub par jayenge, team unhein dekh sakegi.",
      "urdu:native": "آپ کے کمٹس GitHub پر جائیں گے، ٹیم انہیں دیکھ سکے گی۔",
      "hindi:roman": "Aapke commits GitHub par jayenge, team unhein dekh sakegi.",
      "hindi:native": "आपके कमिट GitHub पर जाएंगे, टीम उन्हें देख सकेगी।",
      "dutch": "Stuurt je commits naar GitHub. Het team kan ze dan zien."
    }
  },
  {
    "id": "gh-comment", "risk": "caution",
    "match": "\\bgh\\s+(pr|issue)\\s+(comment|review)\\b|\\bgh\\s+api\\b[^\\n]*comments",
    "text": {
      "english": "Posts a comment on GitHub. The team can see it.",
      "urdu:roman": "GitHub par comment post hoga, team ise dekh sakegi.",
      "urdu:native": "GitHub پر کمنٹ پوسٹ ہو گا، ٹیم اسے دیکھ سکے گی۔",
      "hindi:roman": "GitHub par comment post hoga, team ise dekh sakegi.",
      "hindi:native": "GitHub पर कमेंट पोस्ट होगा, टीम उसे देख सकेगी।",
      "dutch": "Plaatst een reactie op GitHub. Het team kan die zien."
    }
  },
  {
    "id": "gh-pr-create", "risk": "caution",
    "match": "\\bgh\\s+pr\\s+create\\b",
    "text": {
      "english": "Opens a pull request on GitHub. The team will see it.",
      "urdu:roman": "GitHub par pull request khulegi, team ise dekhegi.",
      "urdu:native": "GitHub پر پل ریکویسٹ کھلے گی، ٹیم اسے دیکھے گی۔",
      "hindi:roman": "GitHub par pull request khulegi, team ise dekhegi.",
      "hindi:native": "GitHub पर पुल रिक्वेस्ट खुलेगी, टीम उसे देखेगी।",
      "dutch": "Opent een pull request op GitHub. Het team ziet hem."
    }
  },
  {
    "id": "commit", "risk": "info",
    "match": "\\bgit\\s+commit\\b",
    "text": {
      "english": "Saves the changes as a commit on your computer. Nothing goes to GitHub yet.",
      "urdu:roman": "Changes aapki machine par commit ki shakal mein save honge. Abhi GitHub par kuch nahi jayega.",
      "urdu:native": "چینجز آپ کی مشین پر کمٹ کی صورت میں سیو ہوں گے۔ ابھی GitHub پر کچھ نہیں جائے گا۔",
      "hindi:roman": "Changes aapki machine par commit ke roop mein save honge. Abhi GitHub par kuch nahi jayega.",
      "hindi:native": "बदलाव आपकी मशीन पर कमिट के रूप में सेव होंगे। अभी GitHub पर कुछ नहीं जाएगा।",
      "dutch": "Slaat de wijzigingen op als commit op jouw computer. Er gaat nog niets naar GitHub."
    }
  },
  {
    "id": "install", "risk": "info",
    "match": "\\b(npm|yarn|pnpm)\\s+(install|i|add|ci)\\b|\\bcomposer\\s+(install|require|update)\\b|\\bpip3?\\s+install\\b|\\bbundle\\s+install\\b",
    "text": {
      "english": "Downloads and installs the packages the project needs.",
      "urdu:roman": "Project ke liye zaroori packages download aur install honge.",
      "urdu:native": "پراجیکٹ کے لیے ضروری پیکجز ڈاؤن لوڈ اور انسٹال ہوں گے۔",
      "hindi:roman": "Project ke liye zaroori packages download aur install honge.",
      "hindi:native": "प्रोजेक्ट के लिए ज़रूरी पैकेज डाउनलोड और इंस्टॉल होंगे।",
      "dutch": "Downloadt en installeert de packages die het project nodig heeft."
    }
  },
  {
    "id": "tests", "risk": "info",
    "match": "\\b(npm|yarn|pnpm)\\s+(run\\s+)?test\\b|\\bphpunit\\b|\\bpytest\\b|\\bjest\\b|\\bvitest\\b|\\b(go|cargo)\\s+test\\b|\\bnode\\s+--test\\b",
    "text": {
      "english": "Runs the automated tests. Nothing is changed.",
      "urdu:roman": "Automated tests chalenge. Kuch badlega nahi.",
      "urdu:native": "آٹومیٹڈ ٹیسٹ چلیں گے۔ کچھ نہیں بدلے گا۔",
      "hindi:roman": "Automated tests chalenge. Kuch badlega nahi.",
      "hindi:native": "ऑटोमेटेड टेस्ट चलेंगे। कुछ नहीं बदलेगा।",
      "dutch": "Draait de automatische tests. Er verandert niets."
    }
  }
]
