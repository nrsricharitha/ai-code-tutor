from functools import wraps
import html
import json
import os
import re
import sqlite3
from datetime import datetime

from flask import (
    Flask,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ai-code-tutor-dev-secret")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")


# Expanded with Chinese, Korean, and Japanese
EXPLANATION_LANGUAGES = {
    "english": "English",
    "telugu": "Telugu",
    "hindi": "Hindi",
    "marathi": "Marathi",
    "kannada": "Kannada",
    "tamil": "Tamil",
    "chinese": "Chinese (中文)",
    "korean": "Korean (한국어)",
    "japanese": "Japanese (日本語)",
}

SETUP_LANGUAGES = {
    **EXPLANATION_LANGUAGES,
    "multiple": "Multiple Languages",
}

SKILL_LEVELS = {
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
}

# Expanded with HTML, CSS, and R
CODE_LANGUAGES = {
    "auto": "Auto Detect",
    "python": "Python",
    "c": "C",
    "cpp": "C++",
    "java": "Java",
    "javascript": "JavaScript",
    "html": "HTML",
    "css": "CSS",
    "r": "R Language",
}

CONCEPTS = [
    "Variables",
    "Input",
    "Output",
    "Loops",
    "Conditions",
    "Functions",
    "Arrays",
    "Classes",
    "Objects",
    "Recursion",
]

# Added full translations for Chinese, Korean, and Japanese, plus localized templates
TRANSLATIONS = {
    "english": {
        "overview": "{language} code with {lines} meaningful line(s). It mainly uses {concepts}.",
        "overview_empty": "Enter code to generate an explanation.",
        "line": "Line {line}",
        "variable": "This line stores a value in {name}. The program can reuse that value later.",
        "loop": "This line starts a loop. A loop repeats the same block until its range or condition finishes.",
        "condition": "This line checks a condition and runs a block only when that condition is true.",
        "function": "This line defines a function named {name}. Functions group reusable steps.",
        "class": "This line defines a class named {name}. A class is a blueprint for objects.",
        "array": "This line creates or uses a list/array, which stores multiple values together.",
        "print": "This line displays output so the user can see the result.",
        "return": "This line sends a value back from the current function.",
        "input": "This line accepts input from the user.",
        "include": "This line imports or includes library code so the program can use built-in features.",
        "comment": "This is a comment for humans. It does not run as code.",
        "call": "This line calls a function, which means it asks that function to run.",
        "generic": "This line performs a program step that moves the logic forward.",
        "intermediate_suffix": " At an intermediate level, notice how control flow and data state change here.",
        "advanced_suffix": " Consider time/space complexity, edge cases, and opportunities for optimization here.",
        "no_errors": "No obvious syntax issues were detected by the local checker.",
        "output_unknown": "Output cannot be predicted safely from this snippet.",
        "next": "Practice the detected concepts with small examples, then combine them in one program.",
    },
    "telugu": {
        "overview": "{language} code లో {lines} ముఖ్యమైన line(s) ఉన్నాయి. ఇది ప్రధానంగా {concepts} ఉపయోగిస్తుంది.",
        "overview_empty": "Explanation generate చేయడానికి code enter చేయండి.",
        "line": "లైన్ {line}",
        "variable": "ఈ line {name} లో value store చేస్తుంది. Program దాన్ని తర్వాత మళ్లీ use చేయగలదు.",
        "loop": "ఈ line loop ప్రారంభిస్తుంది. Loop ఒక block ను range లేదా condition పూర్తయ్యే వరకు repeat చేస్తుంది.",
        "condition": "ఈ line condition check చేస్తుంది. Condition true అయితే మాత్రమే block run అవుతుంది.",
        "function": "ఈ line {name} అనే function define చేస్తుంది. Functions reusable steps ను group చేస్తాయి.",
        "class": "ఈ line {name} అనే class define చేస్తుంది. Class objects కోసం blueprint.",
        "array": "ఈ line list/array ను create లేదా use చేస్తుంది. Array అనేక values ను కలిపి store చేస్తుంది.",
        "print": "ఈ line output ను చూపిస్తుంది, user result చూడగలడు.",
        "return": "ఈ line current function నుండి value ను తిరిగి పంపుతుంది.",
        "input": "ఈ line user నుండి input తీసుకుంటుంది.",
        "include": "ఈ line library code ను import/include చేసి built-in features ఉపయోగిస్తుంది.",
        "comment": "ఇది humans కోసం comment. ఇది code లాగా run కాదు.",
        "call": "ఈ line function ను call చేస్తుంది, అంటే ఆ function run అవ్వమని చెబుతుంది.",
        "generic": "ఈ line program logic ను ముందుకు తీసుకెళ్లే step చేస్తుంది.",
        "intermediate_suffix": " Intermediate level లో control flow మరియు data state ఎలా మారుతున్నాయో గమనించండి.",
        "advanced_suffix": " ఇక్కడ time/space complexity, edge cases మరియు optimization అవకాశాలు పరిశీలించండి.",
        "no_errors": "Local checker కి పెద్ద syntax mistakes కనిపించలేదు.",
        "output_unknown": "ఈ snippet output ను safe గా predict చేయలేము.",
        "next": "Detected concepts ను small examples తో practice చేసి, తర్వాత ఒక program లో combine చేయండి.",
    },
    "hindi": {
        "overview": "{language} code में {lines} महत्वपूर्ण line(s) हैं। यह मुख्य रूप से {concepts} उपयोग करता है।",
        "overview_empty": "Explanation generate करने के लिए code डालें।",
        "line": "लाइन {line}",
        "variable": "यह line {name} में value store करती है। Program इसे बाद में फिर use कर सकता है।",
        "loop": "यह line loop शुरू करती है। Loop किसी block को range या condition खत्म होने तक repeat करता है।",
        "condition": "यह line condition check करती है। Condition true होने पर ही block run होता है।",
        "function": "यह line {name} नाम का function define करती है। Functions reusable steps को group करते हैं।",
        "class": "यह line {name} नाम की class define करती है। Class objects के लिए blueprint होती है।",
        "array": "यह line list/array create या use करती है। Array कई values को साथ store करता है।",
        "print": "यह line output दिखाती है ताकि user result देख सके।",
        "return": "यह line current function से value वापस भेजती है।",
        "input": "यह line user से input लेती है।",
        "include": "यह line library code import/include करती है ताकि built-in features use हों।",
        "comment": "यह humans के लिए comment है। यह code की तरह run नहीं होता।",
        "call": "यह line function call करती है, यानी function को run करने के लिए कहती है।",
        "generic": "यह line program logic को आगे बढ़ाने वाला step करती है।",
        "intermediate_suffix": " Intermediate level पर control flow और data state कैसे बदलते हैं, यह देखें।",
        "advanced_suffix": " यहाँ time/space complexity, edge cases और optimization के अवसरों पर विचार करें।",
        "no_errors": "Local checker को कोई obvious syntax issue नहीं मिला।",
        "output_unknown": "इस snippet का output safely predict नहीं किया जा सकता।",
        "next": "Detected concepts को small examples से practice करें, फिर उन्हें एक program में combine करें।",
    },
    "marathi": {
        "overview": "{language} code मध्ये {lines} महत्त्वाच्या line(s) आहेत. हे मुख्यतः {concepts} वापरते.",
        "overview_empty": "Explanation generate करण्यासाठी code लिहा.",
        "line": "लाइन {line}",
        "variable": "ही line {name} मध्ये value store करते. Program ती value नंतर use करू शकतो.",
        "loop": "ही line loop सुरू करते. Loop range किंवा condition संपेपर्यंत block repeat करतो.",
        "condition": "ही line condition check करते. Condition true असेल तरच block run होतो.",
        "function": "ही line {name} नावाचा function define करते. Functions reusable steps group करतात.",
        "class": "ही line {name} नावाची class define करते. Class objects साठी blueprint असते.",
        "array": "ही line list/array create किंवा use करते. Array अनेक values एकत्र store करतो.",
        "print": "ही line output दाखवते, त्यामुळे user result पाहू शकतो.",
        "return": "ही line current function मधून value परत पाठवते.",
        "input": "ही line user कडून input घेते.",
        "include": "ही line library code import/include करते जेणेकरून built-in features वापरता येतील.",
        "comment": "हा humans साठी comment आहे. तो code सारखा run होत नाही.",
        "call": "ही line function call करते, म्हणजे function run करायला सांगते.",
        "generic": "ही line program logic पुढे नेणारा step करते.",
        "intermediate_suffix": " Intermediate level वर control flow आणि data state कसे बदलतात ते पाहा.",
        "advanced_suffix": " येथे time/space complexity, edge cases आणि optimization च्या संधींचा विचार करा.",
        "no_errors": "Local checker ला obvious syntax issue सापडला नाही.",
        "output_unknown": "या snippet चा output safely predict करता येत नाही.",
        "next": "Detected concepts small examples ने practice करा, मग एका program मध्ये combine करा.",
    },
    "kannada": {
        "overview": "{language} code ನಲ್ಲಿ {lines} ಮುಖ್ಯ line(s) ಇವೆ. ಇದು ಮುಖ್ಯವಾಗಿ {concepts} ಬಳಸುತ್ತದೆ.",
        "overview_empty": "Explanation generate ಮಾಡಲು code ನಮೂದಿಸಿ.",
        "line": "ಲೈನ್ {line}",
        "variable": "ಈ line {name} ನಲ್ಲಿ value store ಮಾಡುತ್ತದೆ. Program ಅದನ್ನು ನಂತರ use ಮಾಡಬಹುದು.",
        "loop": "ಈ line loop ಆರಂಭಿಸುತ್ತದೆ. Loop range ಅಥವಾ condition ಮುಗಿಯುವವರೆಗೆ block repeat ಮಾಡುತ್ತದೆ.",
        "condition": "ಈ line condition check ಮಾಡುತ್ತದೆ. Condition true ಆಗಿದ್ದರೆ ಮಾತ್ರ block run ಆಗುತ್ತದೆ.",
        "function": "ಈ line {name} ಎಂಬ function define ಮಾಡುತ್ತದೆ. Functions reusable steps ಅನ್ನು group ಮಾಡುತ್ತವೆ.",
        "class": "ಈ line {name} ಎಂಬ class define ಮಾಡುತ್ತದೆ. Class objects ಗಾಗಿ blueprint.",
        "array": "ಈ line list/array create ಅಥವಾ use ಮಾಡುತ್ತದೆ. Array ಹಲವು values store ಮಾಡುತ್ತದೆ.",
        "print": "ಈ line output ತೋರಿಸುತ್ತದೆ, user result ನೋಡಬಹುದು.",
        "return": "ಈ line current function ನಿಂದ value ಹಿಂದಿರುಗಿಸುತ್ತದೆ.",
        "input": "ಈ line user ಇಂದ input ಪಡೆಯುತ್ತದೆ.",
        "include": "ಈ line library code import/include ಮಾಡಿ built-in features ಬಳಸುತ್ತದೆ.",
        "comment": "ಇದು humans ಗಾಗಿ comment. ಇದು code ಆಗಿ run ಆಗುವುದಿಲ್ಲ.",
        "call": "ಈ line function call ಮಾಡುತ್ತದೆ, ಅಂದರೆ function run ಆಗಲಿ ಎಂದು ಹೇಳುತ್ತದೆ.",
        "generic": "ಈ line program logic ಮುಂದಕ್ಕೆ ಸಾಗುವ step ಮಾಡುತ್ತದೆ.",
        "intermediate_suffix": " Intermediate level ನಲ್ಲಿ control flow ಮತ್ತು data state ಹೇಗೆ ಬದಲಾಗುತ್ತವೆ ನೋಡಿ.",
        "advanced_suffix": " ಇಲ್ಲಿ time/space complexity, edge cases ಮತ್ತು optimization ಅವಕಾಶಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.",
        "no_errors": "Local checker ಗೆ obvious syntax issue ಕಂಡುಬಂದಿಲ್ಲ.",
        "output_unknown": "ಈ snippet output ಅನ್ನು safely predict ಮಾಡಲು ಸಾಧ್ಯವಿಲ್ಲ.",
        "next": "Detected concepts ಅನ್ನು small examples ಮೂಲಕ practice ಮಾಡಿ, ನಂತರ ಒಂದು program ನಲ್ಲಿ combine ಮಾಡಿ.",
    },
    "tamil": {
        "overview": "{language} code-ல் {lines} முக்கிய line(s) உள்ளன. இது முக்கியமாக {concepts} பயன்படுத்துகிறது.",
        "overview_empty": "Explanation generate செய்ய code உள்ளிடுங்கள்.",
        "line": "வரி {line}",
        "variable": "இந்த line {name} இல் value store செய்கிறது. Program பின்னர் அதை use செய்ய முடியும்.",
        "loop": "இந்த line loop தொடங்குகிறது. Loop range அல்லது condition முடியும் வரை block repeat செய்கிறது.",
        "condition": "இந்த line condition check செய்கிறது. Condition true என்றால் மட்டுமே block run ஆகும்.",
        "function": "இந்த line {name} என்ற function define செய்கிறது. Functions reusable steps-ஐ group செய்கின்றன.",
        "class": "இந்த line {name} என்ற class define செய்கிறது. Class objects-க்கு blueprint.",
        "array": "இந்த line list/array create அல்லது use செய்கிறது. Array பல values store செய்கிறது.",
        "print": "இந்த line output காட்டுகிறது, user result பார்க்க முடியும்.",
        "return": "இந்த line current function-இலிருந்து value திரும்ப அனுப்புகிறது.",
        "input": "இந்த line user-இடமிருந்து input பெறுகிறது.",
        "include": "இந்த line library code import/include செய்து built-in features பயன்படுத்துகிறது.",
        "comment": "இது humans-க்கான comment. இது code போல run ஆகாது.",
        "call": "இந்த line function call செய்கிறது, அதாவது function run ஆகச் சொல்கிறது.",
        "generic": "இந்த line program logic முன்னேறும் step செய்கிறது.",
        "intermediate_suffix": " Intermediate level-ல் control flow மற்றும் data state எப்படி மாறுகின்றன கவனியுங்கள்.",
        "advanced_suffix": " இங்கே time/space complexity, edge cases மற்றும் optimization வாய்ப்புகளைப் பரிசீலியுங்கள்.",
        "no_errors": "Local checker obvious syntax issue எதையும் கண்டுபிடிக்கவில்லை.",
        "output_unknown": "இந்த snippet output-ஐ safely predict செய்ய முடியாது.",
        "next": "Detected concepts-ஐ small examples மூலம் practice செய்து, பின்னர் ஒரு program-ல் combine செய்யுங்கள்.",
    },
    "chinese": {
        "overview": "包含 {lines} 行有效代码的 {language} 程序。主要使用了 {concepts}。",
        "overview_empty": "请输入代码以生成解析说明。",
        "line": "第 {line} 行",
        "variable": "此行在变量 {name} 中存储一个值，供程序后续重复使用。",
        "loop": "此行启动一个循环结构，重复执行该代码块直到结束条件满足。",
        "condition": "此行检查条件语句，只有当条件为真 (True) 时才执行对应代码块。",
        "function": "此行定义了一个名为 {name} 的函数，用于封装可重用的步骤。",
        "class": "此行定义了一个名为 {name} 的类，类是创建对象的蓝图。",
        "array": "此行创建或操作一个列表/数组，用于整合存储多个数值。",
        "print": "此行执行输出显示，让用户可以看到运行结果。",
        "return": "此行将数值从当前函数中返回。",
        "input": "此行用于接收来自用户的输入数据。",
        "include": "此行导入或包含库代码，以便程序调用内置功能。",
        "comment": "这是面向开发人员的注释说明，程序运行时不会执行。",
        "call": "此行调用特定的函数来运行其内部封装的逻辑。",
        "generic": "此行执行一个标准的程序步骤以推进业务逻辑。",
        "intermediate_suffix": " 在中级阶段，请注意此处控制流和数据状态的变化。",
        "advanced_suffix": " 在高级阶段，需要考虑此处的时间/空间复杂度、边界条件和优化机会。",
        "no_errors": "本地检查器未检测到明显的语法错误。",
        "output_unknown": "无法从此代码片段安全地预测输出。",
        "next": "通过编写小示例来练习检测到的概念，然后将它们组合在一个程序中。",
    },
    "korean": {
        "overview": "{lines}개의 의미 있는 줄로 구성된 {language} 코드입니다. 주요 개념은 {concepts}입니다.",
        "overview_empty": "설명을 생성하려면 코드를 입력하세요.",
        "line": "{line}번째 줄",
        "variable": "이 줄은 {name} 변수에 값을 저장합니다. 나중에 프로그램에서 이 값을 다시 사용할 수 있습니다.",
        "loop": "이 줄은 반복문(Loop)을 시작합니다. 조건이 충족되거나 범위가 끝날 때까지 블록을 반복합니다.",
        "condition": "이 줄은 조건을 확인하며, 해당 조건이 참(True)일 때만 블록을 실행합니다.",
        "function": "이 줄은 {name} 함수를 정의합니다. 함수는 재사용 가능한 코드 단계를 그룹화합니다.",
        "class": "이 줄은 {name} 클래스를 정의합니다. 클래스는 객체를 만들기 위한 청사진입니다.",
        "array": "이 줄은 여러 값을 함께 저장하는 리스트나 배열을 생성하거나 사용합니다.",
        "print": "이 줄은 사용자가 결과를 볼 수 있도록 출력을 표시합니다.",
        "return": "이 줄은 현재 실행 중인 함수에서 값을 반환합니다.",
        "input": "이 줄은 사용자로부터 입력을 받습니다.",
        "include": "이 줄은 내장 기능을 사용할 수 있도록 외부 라이브러리 코드를 가져오거나 포함합니다.",
        "comment": "이 줄은 사람을 위한 주석입니다. 코드로 실행되지 않습니다.",
        "call": "이 줄은 함수를 호출하여 해당 함수 내부의 로직을 실행합니다.",
        "generic": "이 줄은 프로그램을 전진시키는 일반적인 로직 단계를 수행합니다.",
        "intermediate_suffix": " 중급 레벨에서는 여기서 제어 흐름과 데이터 상태가 어떻게 바뀌는지 주의 깊게 살펴보세요.",
        "advanced_suffix": " 고급 레벨에서는 시간/공간 복잡도, 예외 케이스 및 최적화 요소를 검토하세요.",
        "no_errors": "로컬 검사기에서 발견된 명확한 구문 오류가 없습니다.",
        "output_unknown": "이 코드 조각으로는 출력을 안전하게 예측할 수 없습니다.",
        "next": "탐지된 개념들을 작은 예제로 먼저 연습한 다음, 하나의 프로그램으로 결합해 보세요.",
    },
    "japanese": {
        "overview": "{lines} 行の有効なコードを含む {language} のプログラムです。主に {concepts} が使われています。",
        "overview_empty": "解説を生成するにはコードを入力してください。",
        "line": "{line} 行目",
        "variable": "この行は値を {name} に格納します。プログラムは後でその値を再利用できます。",
        "loop": "この行はループを開始します。範囲または条件が終了するまで同じブロックを繰り返します。",
        "condition": "この行は条件を確認し、その条件が真（True）の場合のみブロックを実行します。",
        "function": "この行は {name} という名前の関数を定義します。関数は再利用可能なステップをまとめます。",
        "class": "この行は {name} という名前のクラスを定義します。クラスはオブジェクトの設計図です。",
        "array": "この行は、複数の値をまとめて格納するリストまたは配列を作成・使用します。",
        "print": "この行は出力を表示し、ユーザーが結果を確認できるようにします。",
        "return": "この行は、現在の関数から値を呼び出し元に返します。",
        "input": "この行はユーザーからの入力を受け付けます。",
        "include": "この行は、組み込み機能を使用するためにライブラリコードをインポートまたはインクルードします。",
        "comment": "これは開発者向けのコメントです。コードとしては実行されません。",
        "call": "この行は関数を呼び出し、その関数を実行します。",
        "generic": "この行は、プログラムのロジックを進める標準的なステップを実行します。",
        "intermediate_suffix": " 中級レベルでは、ここでのコントロールフローとデータ状態の変化に注目してください。",
        "advanced_suffix": " 上級レベルでは、時間・空間複雑度、エッジケース、および最適化の可能性を考慮してください。",
        "no_errors": "ローカルチェッカーで明らかな構文エラーは検出されませんでした。",
        "output_unknown": "このスニペットから出力を安全に予測することはできません。",
        "next": "検出された概念を小さなサンプルで練習し、それらを1つのプログラムに組み合わせてみましょう。",
    }
}


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def add_column_if_missing(conn, table, column, definition):
    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                skill_level TEXT DEFAULT 'beginner',
                preferred_language TEXT DEFAULT 'english',
                setup_complete INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        add_column_if_missing(conn, "users", "skill_level", "TEXT DEFAULT 'beginner'")
        add_column_if_missing(conn, "users", "preferred_language", "TEXT DEFAULT 'english'")
        add_column_if_missing(conn, "users", "setup_complete", "INTEGER DEFAULT 0")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                code TEXT NOT NULL,
                code_language TEXT NOT NULL,
                explanation_language TEXT NOT NULL,
                skill_level TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_explanations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                history_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, history_id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (history_id) REFERENCES analysis_history (id)
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS progress_tracking (
                user_id INTEGER PRIMARY KEY,
                programs_analyzed INTEGER DEFAULT 0,
                total_explanations INTEGER DEFAULT 0,
                concepts_learned TEXT DEFAULT '[]',
                current_level TEXT DEFAULT 'Beginner',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.commit()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def current_user():
    if "user_id" not in session:
        return None
    with get_db_connection() as conn:
        return conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()


def detect_code_language(code, selected="auto"):
    if selected != "auto":
        return selected
    # Enhanced logic mapping for HTML, CSS, and R
    if re.search(r"<!DOCTYPE html>|<html|<body|<div|<p\b", code, re.IGNORECASE):
        return "html"
    if re.search(r"(\{|\bmargin:|\bpadding:|\bbackground-color:|\bcolor:)\s*[^;]+;", code):
        if not re.search(r"\bpublic\s+class\b|\bfunction\b", code):
            return "css"
    if re.search(r"<-|read\.csv\(|ggplot\(|\bdata\.frame\(", code):
        return "r"
    if re.search(r"#include\s*<|std::|cout\s*<<|cin\s*>>", code):
        return "cpp"
    if re.search(r"\bpublic\s+class\b|\bSystem\.out\.println\b|\bstatic\s+void\s+main\b", code):
        return "java"
    if re.search(r"\bfunction\b|console\.log|let\s+|const\s+|=>", code):
        return "javascript"
    if re.search(r"\bprintf\s*\(|\bscanf\s*\(|#include\s*<", code):
        return "c"
    return "python"


def meaningful_lines(code):
    return [(idx, line.rstrip()) for idx, line in enumerate(code.splitlines(), start=1) if line.strip()]


def concept_map(code):
    checks = {
        "Variables": bool(re.search(r"(^|\s)(let|const|var|int|float|double|char|String|bool)\s+\w+|\w+\s*(<-|=)", code)),
        "Input": bool(re.search(r"\b(input|scanf|cin\s*>>|Scanner|readline|gets|fgets|readLines)\b", code)),
        "Output": bool(re.search(r"\b(print|printf|console\.log|System\.out\.println|cout\s*<<|cat\b)", code)) or bool(re.search(r"<p>|<h1>|<span>", code)),
        "Loops": bool(re.search(r"\b(for|while|do|repeat)\b", code)),
        "Conditions": bool(re.search(r"\b(if|else|elif|switch|case)\b", code)),
        "Functions": bool(re.search(r"\b(def|function)\s+\w+|\w+\s*<-\s*function|\w+\s+\w+\s*\([^)]*\)\s*\{", code)),
        "Arrays": bool(re.search(r"\[[^\]]*\]|\b(list|array|vector|ArrayList|c\s*\()\b|\w+\s*\[\s*\]", code)),
        "Classes": bool(re.search(r"\bclass\s+\w+", code)),
        "Objects": bool(re.search(r"\bnew\s+\w+\s*\(|\.\w+\s*\(", code)),
        "Recursion": False,
    }
    function_names = re.findall(r"\b(?:def|function)\s+(\w+)|\b([A-Za-z_]\w*)\s*<-\s*function|\b(?:int|void)\s+(\w+)\s*\(", code)
    names = [a or b or c for a, b, c in function_names]
    checks["Recursion"] = any(len(re.findall(rf"\b{name}\s*\(", code)) > 1 for name in names if name)
    return checks


def detect_line_kind(line, language):
    stripped = line.strip()
    
    # Language-specific Comment/Header Detections
    if language == "html" and stripped.startswith(("")):
        return "comment", {}
    if stripped.startswith(("#", "//", "/*", "*")):
        return "comment", {}
        
    if re.match(r"^(#include|import\s+|from\s+)", stripped):
        return "include", {}
        
    # Dynamic function detection across language scopes
    match = re.search(r"\b(?:def|function)\s+(\w+)|\b([A-Za-z_]\w*)\s*<-\s*function", stripped)
    if match and not re.search(r"\b(if|for|while|switch)\b", stripped):
        return "function", {"name": match.group(1) or match.group(2)}
        
    match = re.search(r"\bclass\s+(\w+)", stripped)
    if match:
        return "class", {"name": match.group(1)}
    if re.search(r"\b(for|while|do|repeat)\b", stripped):
        return "loop", {}
    if re.search(r"\b(if|else if|elif|else|switch|case)\b", stripped):
        return "condition", {}
    if re.search(r"\[[^\]]*\]|\b(vector|ArrayList|c\s*\()\b", stripped):
        return "array", {}
    if re.search(r"\b(print|printf|console\.log|System\.out\.println|cout\s*<<|cat)\b", stripped) or language == "html":
        return "print", {}
    if re.search(r"\breturn\b", stripped):
        return "return", {}
    if re.search(r"\b(input|scanf|cin\s*>>|Scanner|readLines)\b", stripped):
        return "input", {}
        
    assignment = re.search(r"(?:let|const|var|int|float|double|char|String|bool)?\s*([A-Za-z_]\w*)\s*(?:=|<-)", stripped)
    if assignment and "==" not in stripped:
        return "variable", {"name": assignment.group(1)}
    if re.match(r"\w+\s*\(", stripped):
        return "call", {}
    return "generic", {}


def explain_lines(code, level, explanation_language, code_language):
    phrases = TRANSLATIONS[explanation_language]
    items = []
    for line_number, line in meaningful_lines(code):
        kind, details = detect_line_kind(line, code_language)
        text = phrases[kind].format(**details)
        if level == "intermediate" and kind not in {"comment", "generic"}:
            text += phrases["intermediate_suffix"]
        elif level == "advanced" and kind not in {"comment", "generic"}:
            text += phrases["advanced_suffix"]
        items.append(
            {
                "line": line_number,
                "title": phrases["line"].format(line=line_number),
                "code": line.strip(),
                "kind": kind,
                "explanation": text,
            }
        )
    return items


def detect_errors(code, code_language):
    errors = []
    
    # HTML and CSS brackets rules logic
    if code_language == "html":
        if code.count("<") != code.count(">"):
            errors.append({
                "line": "-",
                "description": "Unbalanced HTML tag angled brackets detected.",
                "fix": "Ensure every opening '<' matches a closing '>' tag safely."
            })
        return errors if errors else [{"line": "-", "description": TRANSLATIONS["english"]["no_errors"], "fix": "No action needed."}]

    pairs = [("(", ")"), ("[", "]"), ("{", "}")]
    for open_char, close_char in pairs:
        if code.count(open_char) != code.count(close_char):
            errors.append(
                {
                    "line": "-",
                    "description": f"Unbalanced {open_char}{close_char} brackets.",
                    "fix": f"Check that every {open_char} has a matching {close_char}.",
                }
            )

    lines = meaningful_lines(code)
    for line_number, line in lines:
        stripped = line.strip()
        if code_language == "python":
            if re.match(r"^(if|elif|else|for|while|def|class)\b", stripped) and not stripped.endswith(":"):
                errors.append(
                    {
                        "line": line_number,
                        "description": "Python block statement is missing a colon.",
                        "fix": "Add ':' at the end of the line.",
                    }
                )
        elif code_language in {"c", "cpp", "java", "javascript", "css"}:
            needs_semicolon = (
                stripped
                and not stripped.endswith((";", "{", "}", ":", ","))
                and not re.match(r"^(if|for|while|else|switch|class|public|private|function)\b", stripped)
                and not stripped.startswith(("//", "#include", "import"))
            )
            if needs_semicolon:
                errors.append(
                    {
                        "line": line_number,
                        "description": "This statement may be missing a semicolon or property closer.",
                        "fix": "Add ';' at the end if this is a complete statement block.",
                    }
                )
    if not errors:
        errors.append({"line": "-", "description": TRANSLATIONS["english"]["no_errors"], "fix": "No action needed."})
    return errors


def complexity(code, concepts):
    line_count = len(meaningful_lines(code))
    advanced_concepts = sum(1 for k in ["Recursion", "Classes", "Objects"] if concepts.get(k))
    intermediate_concepts = sum(1 for k in ["Functions", "Arrays"] if concepts.get(k))
    basic_concepts = sum(1 for k in ["Variables", "Input", "Output", "Loops", "Conditions"] if concepts.get(k))

    nesting = 0
    if code.strip():
        nesting = max((len(line) - len(line.lstrip(" "))) // 4 for _, line in meaningful_lines(code))

    loop_count = len(re.findall(r"\b(for|while|do|repeat)\b", code))
    func_count = len(re.findall(r"\b(def|function)\s+\w+|\w+\s*<-\s*function", code))

    score = (
        basic_concepts * 1
        + intermediate_concepts * 2
        + advanced_concepts * 3
        + (1 if loop_count > 1 else 0)
        + (1 if nesting >= 2 else 0)
        + (1 if func_count > 1 else 0)
        + line_count // 10
    )
    score = min(10, max(1, score))

    if advanced_concepts >= 1 or (intermediate_concepts >= 2 and loop_count >= 2) or score >= 7:
        level = "Advanced"
        reason = "Uses functional scaling recursion, structures, or advanced pipeline frameworks."
    elif intermediate_concepts >= 1 or loop_count > 1 or func_count >= 1 or score >= 4:
        level = "Intermediate"
        reason = "Uses structured functions, lists, iterations, or layout trees."
    else:
        level = "Beginner"
        reason = "Uses fundamental single-step variables, style markers, or direct prints."

    return {"level": level, "score": score, "reason": reason}


def predict_output(code, code_language, explanation_language):
    prints = []
    variables = {}
    execution_stack = [True] 
    lines = [line.strip().rstrip(";") for _, line in meaningful_lines(code)]
    
    for stripped in lines:
        if not stripped:
            continue
        if stripped == "}" or stripped == "":
            if len(execution_stack) > 1:
                execution_stack.pop()
            continue

        # Handle Assignment compatibility with R language (<-)
        assign = re.match(r"^(?:(?:let|const|var|int|float|double|char|String|bool)\s+)?([A-Za-z_]\w*)\s*(?:=|<-)\s*(.*)$", stripped)
        if assign and "==" not in stripped:
            var_name = assign.group(1)
            var_val_expr = assign.group(2).strip().strip("\"'")
            if execution_stack[-1]:
                try:
                    variables[var_name] = int(var_val_expr)
                except ValueError:
                    variables[var_name] = var_val_expr

        if_match = re.match(r"^if\s*\((.*)\)\s*\{?", stripped) or re.match(r"^if\s+(.*):", stripped)
        if if_match:
            cond_expr = if_match.group(1).strip()
            cond_expr = cond_expr.replace("&&", " and ").replace("||", " or ")
            for k, v in variables.items():
                cond_expr = re.sub(rf"\b{k}\b", str(repr(v) if isinstance(v, str) else v), cond_expr)
            try:
                result = bool(eval(cond_expr, {"__builtins__": None}, variables))
            except Exception:
                result = True
            execution_stack.append(result and execution_stack[-1])
            continue

        if stripped.startswith("else") or stripped.startswith("elif"):
            if len(execution_stack) > 1:
                prev_cond = execution_stack.pop()
                execution_stack.append((not prev_cond) and (execution_stack[-1] if len(execution_stack) > 0 else True))
            continue

        if execution_stack[-1]:
            print_match = re.search(
                r"(?:print|printf|console\.log|System\.out\.println|cat)\s*\((.*?)\)|cout\s*<<\s*(.*)",
                stripped,
            )
            if print_match:
                value = (print_match.group(1) or print_match.group(2) or "").strip()
                value = value.replace("\\n", "").strip("\"'")
                resolved = re.sub(r"\{(\w+)\}", lambda m: str(variables.get(m.group(1), m.group(1))), value)
                resolved = str(variables.get(resolved, resolved))
                if resolved and not any(c in resolved for c in ["(", "+", "%"]):
                    prints.append(resolved)

    if prints:
        return "\n".join(prints)
    return TRANSLATIONS[explanation_language]["output_unknown"]


def roadmap(concepts):
    next_topics = []
    if concepts.get("Loops") and not concepts.get("Arrays"):
        next_topics.append("Learn Array Traversal with Loops")
    if concepts.get("Loops"):
        next_topics.append("Practice Nested Loops")
    if concepts.get("Functions"):
        next_topics.append("Learn Function Parameters & Return Values")
    if not concepts.get("Functions"):
        next_topics.append("Introduction to Functions")
    if not next_topics:
        next_topics = ["Introduction to Functions", "Arrays & Lists", "OOP Basics", "Data Structures"]
    seen = set()
    result = []
    for t in next_topics:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result[:6]


def quiz_questions(concepts, output):
    questions = []
    if concepts.get("Loops"):
        questions.append({
            "question": "What is the primary purpose of a loop in a program?",
            "options": ["Store data in memory", "Repeat a block of instructions", "Define a new function", "Delete a variable"],
            "answer": 1,
        })
    if concepts.get("Variables"):
        questions.append({
            "question": "What does a variable do in a program?",
            "options": ["Runs the program faster", "Stores a value for later use", "Creates a loop", "Ends the program"],
            "answer": 1,
        })
    questions.append({
        "question": "What is the expected output of this program?",
        "options": [output[:40] if output and "cannot" not in output else "Varies", "No output", "An error", "Infinite loop"],
        "answer": 0 if output and "cannot" not in output else 2,
    })
    return questions[:5]


def analyze_code(code, code_language, explanation_language, skill_level):
    explanation_language = explanation_language if explanation_language in TRANSLATIONS else "english"
    skill_level = skill_level if skill_level in SKILL_LEVELS else "beginner"
    detected_language = detect_code_language(code, code_language)
    lines = meaningful_lines(code)
    concepts = concept_map(code)
    concept_list = [name for name, enabled in concepts.items() if enabled]
    phrases = TRANSLATIONS[explanation_language]
    overview = (
        phrases["overview_empty"]
        if not lines
        else phrases["overview"].format(
            language=CODE_LANGUAGES.get(detected_language, detected_language.title()),
            lines=len(lines),
            concepts=", ".join(concept_list) if concept_list else "basic programming steps",
        )
    )
    output = predict_output(code, detected_language, explanation_language)
    result = {
        "overview": overview,
        "items": explain_lines(code, skill_level, explanation_language, detected_language),
        "errors": detect_errors(code, detected_language),
        "concepts": concepts,
        "complexity": complexity(code, concepts),
        "expected_output": output,
        "roadmap": roadmap(concepts),
        "quiz": quiz_questions(concepts, output),
        "code_language": detected_language,
        "explanation_language": explanation_language,
        "skill_level": skill_level,
        "created_at": datetime.now().strftime("%d %b %Y, %I:%M %p"),
    }
    return result


def update_progress(user_id, result):
    learned = [name for name, enabled in result["concepts"].items() if enabled]
    with get_db_connection() as conn:
        progress = conn.execute(
            "SELECT * FROM progress_tracking WHERE user_id = ?", (user_id,)
        ).fetchone()
        if progress:
            existing = set(json.loads(progress["concepts_learned"] or "[]"))
            existing.update(learned)
            programs = progress["programs_analyzed"] + 1
            total = progress["total_explanations"] + 1
            conn.execute(
                """
                UPDATE progress_tracking
                SET programs_analyzed = ?, total_explanations = ?, concepts_learned = ?,
                    current_level = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (programs, total, json.dumps(sorted(existing)), result["complexity"]["level"], user_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO progress_tracking
                (user_id, programs_analyzed, total_explanations, concepts_learned, current_level)
                VALUES (?, 1, 1, ?, ?)
                """,
                (user_id, json.dumps(sorted(learned)), result["complexity"]["level"]),
            )
        conn.commit()


def store_history(user_id, code, code_language, explanation_language, skill_level, result):
    first_line = code.strip().splitlines()[0][:50] if code.strip() else "Untitled"
    title = f"{first_line}"
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO analysis_history
            (user_id, title, code, code_language, explanation_language, skill_level, result_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, title, code, code_language, explanation_language, skill_level, json.dumps(result)),
        )
        conn.commit()
        return cursor.lastrowid


def dashboard_data(user_id):
    with get_db_connection() as conn:
        history = conn.execute(
            """
            SELECT id, title, code_language, explanation_language, skill_level, created_at
            FROM analysis_history WHERE user_id = ?
            ORDER BY id DESC LIMIT 10
            """,
            (user_id,),
        ).fetchall()
        favorites = conn.execute(
            """
            SELECT s.id, s.history_id, s.title, s.created_at
            FROM saved_explanations s
            WHERE s.user_id = ?
            ORDER BY s.id DESC LIMIT 10
            """,
            (user_id,),
        ).fetchall()
        progress = conn.execute("SELECT * FROM progress_tracking WHERE user_id = ?", (user_id,)).fetchone()
    if not progress:
        progress = {
            "programs_analyzed": 0,
            "total_explanations": 0,
            "concepts_learned": "[]",
            "current_level": "Beginner",
        }
    return history, favorites, progress


def pdf_escape(text):
    return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_simple_pdf(title, lines):
    catalog_obj = "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj"
    pages_obj = "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj"
    font_obj = "4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj"
    
    y = 740
    commands = ["BT", "/F1 16 Tf", f"50 {y} Td", f"({pdf_escape(title)}) Tj", "0 -24 Td"]
    y -= 24
    commands.append("/F1 10 Tf")
    
    for raw_line in lines:
        if not raw_line.strip():
            commands.append("0 -14 Td")
            y -= 14
            continue
        for chunk in re.findall(".{1,85}", str(raw_line)) or [""]:
            commands.append(f"({pdf_escape(chunk)}) Tj")
            commands.append("0 -14 Td")
            y -= 14
            if y < 50:
                break
        if y < 50:
            break
            
    commands.append("ET")
    stream_content = "\n".join(commands)
    
    content_obj = f"5 0 obj\n<< /Length {len(stream_content.encode('utf-8'))} >>\nstream\n{stream_content}\nendstream\nendobj"
    page_obj = "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj"
    
    pdf_parts = [
        "%PDF-1.4",
        catalog_obj,
        pages_obj,
        page_obj,
        font_obj,
        content_obj
    ]
    
    body = "\n".join(pdf_parts) + "\n"
    offsets = []
    lines_list = body.splitlines()
    
    pdf_out = bytearray()
    for line in lines_list:
        offsets.append(len(pdf_out))
        pdf_out.extend((line + "\n").encode("utf-8"))
        
    xref_pos = len(pdf_out)
    xref_table = [
        "xref",
        f"0 {len(pdf_parts)}",
        "0000000000 65535 f "
    ]
    
    for idx in range(1, len(pdf_parts)):
        xref_table.append(f"{offsets[idx]:010d} 00000 n ")
        
    xref_table.append(f"trailer\n<< /Size {len(pdf_parts)} /Root 1 0 R >>")
    xref_table.append(f"startxref\n{xref_pos}\n%%EOF")
    
    pdf_out.extend(("\n".join(xref_table)).encode("utf-8"))
    return bytes(pdf_out)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not full_name or not email or not password or not confirm_password:
            flash("Please fill in every field.", "danger")
        elif password != confirm_password:
            flash("Passwords do not match.", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        else:
            try:
                with get_db_connection() as conn:
                    cursor = conn.execute(
                        "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
                        (full_name, email, generate_password_hash(password)),
                    )
                    conn.commit()
                session.clear()
                session["user_id"] = cursor.lastrowid
                session["user_name"] = full_name
                return redirect(url_for("setup"))
            except sqlite3.IntegrityError:
                flash("An account with this email already exists.", "danger")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db_connection() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            if not user["setup_complete"]:
                return redirect(url_for("setup"))
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/setup", methods=["GET", "POST"])
@login_required
def setup():
    if request.method == "POST":
        skill_level = request.form.get("skill_level", "beginner")
        preferred_language = request.form.get("preferred_language", "english")
        if skill_level not in SKILL_LEVELS:
            skill_level = "beginner"
        if preferred_language not in SETUP_LANGUAGES:
            preferred_language = "english"
        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET skill_level = ?, preferred_language = ?, setup_complete = 1
                WHERE id = ?
                """,
                (skill_level, preferred_language, session["user_id"]),
            )
            conn.commit()
        return redirect(url_for("dashboard"))
    return render_template("setup.html", skill_levels=SKILL_LEVELS, languages=SETUP_LANGUAGES)


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("home"))


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        with get_db_connection() as conn:
            user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            flash("Email not found.", "danger")
            return render_template("forgot_password.html")
        session["reset_email"] = email
        return redirect(url_for("reset_password"))
    return render_template("forgot_password.html")


@app.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    reset_email = session.get("reset_email")
    if not reset_email:
        flash("Please verify your email first.", "warning")
        return redirect(url_for("forgot_password"))
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
        else:
            with get_db_connection() as conn:
                conn.execute(
                    "UPDATE users SET password_hash = ? WHERE email = ?",
                    (generate_password_hash(password), reset_email),
                )
                conn.commit()
            session.pop("reset_email", None)
            flash("Password updated successfully.", "success")
            return redirect(url_for("login"))
    return render_template("reset_password.html", email=reset_email)


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    history, favorites, progress = dashboard_data(session["user_id"])
    preferred = user["preferred_language"] if user["preferred_language"] in EXPLANATION_LANGUAGES else "english"
    return render_template(
        "dashboard.html",
        user=user,
        history=history,
        favorites=favorites,
        progress=progress,
        concepts_learned=json.loads(progress["concepts_learned"] or "[]"),
        explanation_languages=EXPLANATION_LANGUAGES,
        code_languages=CODE_LANGUAGES,
        skill_levels=SKILL_LEVELS,
        preferred_language=preferred,
    )


@app.route("/explain-code", methods=["POST"])
@login_required
def explain_code():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "")
    code_language = data.get("code_language", "auto")
    explanation_language = data.get("language", "english")
    skill_level = data.get("level", "beginner")
    result = analyze_code(code, code_language, explanation_language, skill_level)
    if code.strip():
        history_id = store_history(
            session["user_id"], code, result["code_language"], explanation_language, skill_level, result
        )
        update_progress(session["user_id"], result)
        result["history_id"] = history_id
    return jsonify(result)


@app.route("/history/<int:history_id>")
@login_required
def get_history(history_id):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analysis_history WHERE id = ? AND user_id = ?",
            (history_id, session["user_id"]),
        ).fetchone()
    if not row:
        return jsonify({"error": "History not found."}), 404
    result = json.loads(row["result_json"])
    result["history_id"] = row["id"]
    result["code"] = row["code"]
    return jsonify(result)


@app.route("/favorite/<int:history_id>", methods=["POST"])
@login_required
def favorite(history_id):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT title FROM analysis_history WHERE id = ? AND user_id = ?",
            (history_id, session["user_id"]),
        ).fetchone()
        if not row:
            return jsonify({"error": "History not found."}), 404
        conn.execute(
            """
            INSERT OR IGNORE INTO saved_explanations (user_id, history_id, title)
            VALUES (?, ?, ?)
            """,
            (session["user_id"], history_id, row["title"]),
        )
        conn.commit()
    return jsonify({"saved": True})


@app.route("/download/<int:history_id>")
@login_required
def download_pdf(history_id):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM analysis_history WHERE id = ? AND user_id = ?",
            (history_id, session["user_id"]),
        ).fetchone()
    if not row:
        flash("Analysis not found.", "danger")
        return redirect(url_for("dashboard"))
        
    result = json.loads(row["result_json"])
    
    lines = [
        f"Programming Language: {row['code_language'].upper()}",
        f"Skill Level: {row['skill_level'].upper()}",
        "",
        "--- SUBMITTED CODE ---",
    ]
    lines.extend(row["code"].splitlines())
    lines.extend([
        "",
        "--- OVERVIEW ---",
        result['overview'],
        "",
        "--- LINE-BY-LINE EXPLANATION ---"
    ])
    lines.extend(f"{item['title']}: [{item['code']}] -> {item['explanation']}" for item in result["items"])
    lines.extend([
        "",
        "--- COMPLEXITY ANALYSIS ---",
        f"Complexity Level: {result['complexity']['level']} ({result['complexity']['score']}/10)",
        f"Reasoning: {result['complexity']['reason']}",
        "",
        "--- ERROR DETECTION ---"
    ])
    lines.extend(f"Line {err['line']}: {err['description']} (Fix: {err['fix']})" for err in result["errors"])
    lines.extend([
        "",
        "--- EXPECTED OUTPUT ---",
        result['expected_output'],
        "",
        "--- LEARNING ROADMAP ---"
    ])
    lines.extend(f"- {topic}" for topic in result["roadmap"])
    lines.extend([
        "",
        "--- PRACTICE QUIZ ---"
    ])
    for q in result["quiz"]:
        if isinstance(q, dict):
            lines.append(f"Question: {q['question']}")
            for i, opt in enumerate(q.get('options', [])):
                lines.append(f"  {'ABCD'[i]}. {opt}")
        else:
            lines.append(f"- {q}")
            
    response = make_response(make_simple_pdf("AI Code Tutor Explanation", lines))
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename=ai-code-tutor-{history_id}.pdf"
    return response


@app.template_filter("pretty_json")
def pretty_json(value):
    return html.escape(json.dumps(value, indent=2))


init_db()


if __name__ == "__main__":
    app.run(debug=True)
