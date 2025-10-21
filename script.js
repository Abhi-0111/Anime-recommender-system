// Main App Elements
const recommendationsContainer = document.getElementById('recommendations');
const loadingIndicator = document.getElementById('loading');
const errorMessage = document.getElementById('error-message');
const modal = document.getElementById('modal');
const modalOverlay = document.getElementById('modal-overlay');
const modalCloseBtn = document.getElementById('modal-close-btn');
const modalBody = document.getElementById('modal-body');
const genreFilter = document.getElementById('genre-filter');
const randomBtn = document.getElementById('random-btn');
const resetBtn = document.getElementById('reset-btn');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');

// Chatbot Elements
const chatbotToggle = document.getElementById('chatbot-toggle');
const chatWindow = document.getElementById('chat-window');
const chatMessages = document.getElementById('chat-messages');
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send-btn');

const API_URL = 'http://127.0.0.1:5000/api';

// --- Main App Logic ---
function displayResults(animeList, container, message) {
    container.innerHTML = '';
    if (!animeList || animeList.length === 0) {
        container.innerHTML = `<p class="text-gray-400 col-span-full">${message}</p>`;
    } else {
         animeList.forEach(anime => container.appendChild(createAnimeCard(anime)));
    }
}

async function fetchAndDisplayAnime(genre = '') {
    loadingIndicator.classList.remove('hidden');
    recommendationsContainer.innerHTML = '';
    errorMessage.classList.add('hidden');
    let url = `${API_URL}/anime${genre ? `?genre=${encodeURIComponent(genre)}` : ''}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Network response was not ok');
        displayResults(await response.json(), recommendationsContainer, 'No anime found.');
    } catch (error) {
        console.error('Error fetching anime:', error);
        errorMessage.textContent = 'Could not connect to the backend.';
        errorMessage.classList.remove('hidden');
    } finally {
        loadingIndicator.classList.add('hidden');
    }
}

async function searchAnime() {
    const query = searchInput.value.trim();
    if (!query) return;
    loadingIndicator.classList.remove('hidden');
    recommendationsContainer.innerHTML = '';
    errorMessage.classList.add('hidden');
    genreFilter.value = '';
    try {
        const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error('Search failed');
        displayResults(await response.json(), recommendationsContainer, `No results for "${query}".`);
    } catch (error) { console.error('Error:', error); } 
    finally { loadingIndicator.classList.add('hidden'); }
}

async function populateGenres() {
    try {
        const response = await fetch(`${API_URL}/genres`);
        const genres = await response.json();
        genres.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g; opt.textContent = g; genreFilter.appendChild(opt);
        });
    } catch (e) { console.error("Genre load failed", e); }
}

function createAnimeCard(anime) {
    const card = document.createElement('div');
    card.className = 'card rounded-lg overflow-hidden p-5 text-left cursor-pointer';
    card.dataset.title = anime.name;
    const imageUrl = anime.image_url || `https://placehold.co/300x450/1a1a2e/fff?text=${encodeURIComponent(anime.name)}`;
    const mainGenre = anime.genre ? anime.genre.split(',')[0] : 'N/A';
    card.innerHTML = `<img class="w-full h-auto aspect-[2/3] object-cover rounded-md mb-4" src="${imageUrl}" onerror="this.onerror=null;this.src='https://placehold.co/300x450/1a1a2e/fff?text=Not+Found';"><h3 class="text-xl font-bold mb-2 truncate">${anime.name}</h3><div><span class="inline-block bg-pink-600/50 rounded-full px-3 py-1 text-xs font-semibold text-white">${mainGenre}</span></div>`;
    return card;
}

 async function showRecommendationsModal(title) {
    modalBody.innerHTML = `<div class="flex justify-center items-center h-64"><div class="loader"></div></div>`;
    modal.classList.remove('hidden');
    try {
        const response = await fetch(`${API_URL}/recommend?title=${encodeURIComponent(title)}`);
        const recommendations = await response.json();
        if (recommendations.error) throw new Error(recommendations.error);
        modalBody.innerHTML = `<h2 class="text-3xl font-bold mb-4">Because you watched <span class="text-pink-400">${title}</span></h2><div class="space-y-3">${recommendations.map(rec => { const imageUrl = rec.image_url || `https://placehold.co/80x120/16213e/e94560?text=${encodeURIComponent(rec.name)}`; return `<div class="flex items-center bg-gray-800/50 p-3 rounded-lg"><img src="${imageUrl}" onerror="this.onerror=null;this.src='https://placehold.co/80x120/16213e/e94560?text=Not+Found';" class="w-16 h-24 object-cover rounded-md mr-4"><div><h4 class="font-bold text-lg">${rec.name}</h4><p class="text-sm text-gray-400">${rec.genre}</p><p class="text-sm text-yellow-400">Rating: ${rec.rating ? rec.rating.toFixed(2) : 'N/A'}</p></div></div>` }).join('') || '<p>No similar anime found.</p>'}</div>`;
    } catch (error) { modalBody.innerHTML = `<p class="text-red-400 text-center">Could not load recommendations.</p>`; console.error(error); }
}

async function fetchRandomAnime() {
    loadingIndicator.classList.remove('hidden');
    recommendationsContainer.innerHTML = '';
    errorMessage.classList.add('hidden');
    try {
         const response = await fetch(`${API_URL}/random`);
         const anime = await response.json();
         showRecommendationsModal(anime.name);
    } catch(e) {
        console.error("Failed to fetch random anime", e);
    } finally {
        loadingIndicator.classList.add('hidden');
        // We fetch the main list again after closing the modal, so no need to reload here
    }
}

function closeModal() { modal.classList.add('hidden'); }

// --- Chatbot Logic ---
function addMessage(content, isUser = false) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble p-3 rounded-lg ${isUser ? 'user-bubble self-end' : 'bot-bubble self-start'}`;
    bubble.innerHTML = content;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    const typingBubble = document.createElement('div');
    typingBubble.id = 'typing-indicator';
    typingBubble.className = 'bot-bubble self-start p-3 rounded-lg typing-indicator';
    typingBubble.innerHTML = '<span></span><span></span><span></span>';
    chatMessages.appendChild(typingBubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function createChatAnimeCards(animeList) {
    if (!animeList || animeList.length === 0) return '';
    return `<div class="flex gap-2 overflow-x-auto p-1 mt-2">${animeList.map(anime => {
        const imageUrl = anime.image_url || `https://placehold.co/100x150/16213e/e94560?text=N/A`;
        return `<div class="flex-shrink-0 w-24 text-center"><img src="${imageUrl}" class="w-24 h-36 object-cover rounded-md" onerror="this.onerror=null;this.src='https://placehold.co/100x150/16213e/e94560?text=N/A';"><p class="text-xs mt-1 truncate">${anime.name}</p></div>`
    }).join('')}</div>`;
}

async function handleSendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;
    addMessage(message, true);
    chatInput.value = '';
    showTypingIndicator();

    try {
        const response = await fetch(`${API_URL}/chatbot`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });
        const data = await response.json();
        removeTypingIndicator();
        addMessage(data.reply + createChatAnimeCards(data.anime_list));
    } catch (error) {
        removeTypingIndicator();
        addMessage("Oops! I couldn't connect to my brain. Please try again.");
        console.error("Chatbot error:", error);
    }
}

// --- Event Listeners ---
document.addEventListener('DOMContentLoaded', () => { populateGenres(); fetchAndDisplayAnime(); });
searchBtn.addEventListener('click', searchAnime);
searchInput.addEventListener('keyup', (e) => e.key === 'Enter' && searchAnime());
recommendationsContainer.addEventListener('click', (e) => e.target.closest('.card')?.dataset.title && showRecommendationsModal(e.target.closest('.card').dataset.title));
genreFilter.addEventListener('change', (e) => { searchInput.value = ''; fetchAndDisplayAnime(e.target.value); });
resetBtn.addEventListener('click', () => { genreFilter.value = ''; searchInput.value = ''; fetchAndDisplayAnime(); });
randomBtn.addEventListener('click', fetchRandomAnime);
modalCloseBtn.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', closeModal);
// Chatbot listeners
chatbotToggle.addEventListener('click', () => chatWindow.classList.toggle('hidden'));
chatSendBtn.addEventListener('click', handleSendMessage);
chatInput.addEventListener('keyup', (e) => e.key === 'Enter' && handleSendMessage());
