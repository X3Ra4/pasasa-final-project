# Відповідність завданню

| Вимога | Реалізація / як перевірити |
|---|---|
| React Native + Expo, create-expo-app | package.json, app.json; початковий коміт scaffold |
| Expo Router, ≥4 екрани, вкладки | 4 Tabs + деталі + форма + onboarding |
| Динамічний маршрут поверх попереднього | Stack `meal/[id]`; картка передає лише ID |
| Осмислені push/replace | push відкриває рецепт/форму; replace завершує onboarding/форму |
| Реальний API | src/core/api.ts, TheMealDB HTTPS |
| Серверний пошук/фільтр | search.php та filter.php, не локальний filter каталогу |
| Loading/error/retry/empty | useRequest, Loading, ErrorState, Empty; E2E 503 і порожня відповідь |
| FlatList, keyExtractor, ListEmptyComponent | головний каталог, обране, покупки, інгредієнти |
| Pull-to-refresh | каталог і обране |
| TextInput + валідація | shopping/new: назва обов'язкова ≤80, кількість ≤40; нотатка ≤1000 |
| Context | AppContext на рівні кореневого Layout |
| AsyncStorage | @smak/state:v1, відновлення перед відкриттям екранів |
| ≥3 анімації | пружне стискання кнопки, fade/translate появи, пульсація skeleton, fade придбаного |
| Різні ширини й орієнтації | orientation: default; useWindowDimensions, 1–3 колонки, maxWidth, safe-area |
| Git, README, 4–6 знімків | README містить 6 знімків, історію змін і запуск |
| .gitignore | node_modules, .env, приватні ключі, native build output |
| Бонус: тема | темна/світла зберігається між запусками |
| Бонус: offline | повні обрані рецепти, покупки, нотатки; банер мережі |
| Бонус: onboarding/cache | перший запуск, expo-image memory-disk + fallback |
| Надійність | валідація API/сховища, timeout/abort, послідовні записи, збереження попереднього стану при помилці |

Зміни не названі «оптимістичними»: стан публікується лише після успішного запису.
Пошкоджене сховище не стирається автоматично. Повторний імпорт не дублює
інгредієнти того самого рецепта; продукти різних рецептів не об'єднуються,
оскільки одиниці вимірювання можуть відрізнятися.

Живу демонстрацію та відповіді на запитання студент виконує особисто.
Автоматичний Android smoke перевіряє запуск/onboarding/каталог, а не всі
нативні жести. Pull-to-refresh і фізичний поворот включені до сценарію захисту.
