// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {

    // --- Page Transition Logic ---
    document.body.classList.add('is-loaded');
    const allLinks = document.querySelectorAll('a');
    allLinks.forEach(link => {
        link.addEventListener('click', e => {
            const destination = link.getAttribute('href');
            if (destination && destination !== '#' && !destination.startsWith('javascript:')) {
                e.preventDefault();
                document.body.classList.remove('is-loaded');
                setTimeout(() => { window.location.href = destination; }, 500);
            }
        });
    });
    window.addEventListener('pageshow', event => {
        if (event.persisted) {
            document.body.classList.add('is-loaded');
        }
    });

    // --- Assessment-Specific Logic ---
    const questions = [
        { q: "1. When faced with a high-pressure situation, do you prioritize your tasks and decisions?", o: ["Never prioritize", "Rarely", "Sometimes", "Often prioritize", "Always prioritize"] },
        { q: "2. What is your approach when you face a task that initially seems impossible?", o: ["Ignore the challenge", "Feel overwhelmed", "Think before acting", "Try despite doubts", "Accept the challenge"] },
        { q: "3. How do you manage stress in situations beyond your control?", o: ["I get annoyed", "Easily upset", "Somewhat stressed", "Stay calm", "I manage stress"] },
        { q: "4. Do you view past adversity as a learning experience?", o: ["Never", "Rarely", "Sometimes", "Often", "Always"] },
        { q: "5. How do you handle criticism from others?", o: ["Take it personally", "Defend yourself", "Disregard it", "Reflect and adapt", "Acknowledge and grow"] },
        { q: "6. Your response to a major change in life?", o: ["Feel overwhelmed", "Deny it", "Seek support", "Assess it calmly", "Embrace and plan"] },
        { q: "7. How do you adapt to life changes?", o: ["Resist and dwell on the past", "Ignore changes", "Embrace new chances", "Take small steps", "Proactively adapt"] },
        { q: "8. Do you adjust goals when unexpected changes occur?", o: ["Never adjust", "Rarely", "Sometimes", "Often adjust", "Always adjust"] },
        { q: "9. Are you comfortable in uncertain situations?", o: ["Cannot work", "Slightly uncomfortable", "Neutral", "Mostly okay", "Very comfortable"] },
        { q: "10. Do you maintain positive relationships during adversity?", o: ["Never", "Rarely", "Sometimes", "Often", "Always"] },
        { q: "11. Do you stay optimistic during challenging times?", o: ["Never", "Rarely", "Sometimes", "Often", "Always"] },
        { q: "12. Being criticized for a subject assignment:", o: ["Affects all aspects of life", "Affects many areas", "Affects some areas", "Affects only this area", "Limited to the situation"] },
        { q: "13. Missing a flight or a train:", o: ["Affects all aspects of life", "Affects many areas", "Affects some areas", "Affects only this area", "Limited to the situation"] },
        { q: "14. Having multiple setbacks in one day:", o: ["Affects all aspects of life", "Affects many areas", "Affects some areas", "Affects only this area", "Limited to the situation"] },
        { q: "15. Arguing with someone and developing negative emotions:", o: ["Affects all aspects of life", "Affects many areas", "Affects some areas", "Affects only this area", "Limited to the situation"] },
        { q: "16. Your teacher adamantly disagrees with your idea:", o: ["Affects all aspects of life", "Affects many areas", "Affects some areas", "Affects only this area", "Limited to the situation"] },
        { q: "17. An important activity gets canceled:", o: ["Least relevant", "Slightly relevant", "Moderately relevant", "Very relevant", "Most relevant"] },
        { q: "18. You lose something crucial to your well-being:", o: ["Least relevant", "Slightly relevant", "Moderately relevant", "Very relevant", "Most relevant"] },
        { q: "19. You miss an important appointment:", o: ["Least relevant", "Slightly relevant", "Moderately relevant", "Very relevant", "Most relevant"] },
        { q: "20. You message a friend, they see it but don't reply:", o: ["Least relevant", "Slightly relevant", "Moderately relevant", "Very relevant", "Most relevant"] },
        { q: "21. You accidentally delete an important message:", o: ["Least relevant", "Slightly relevant", "Moderately relevant", "Very relevant", "Most relevant"] },
        { q: "22. How do you react to a significant failure?", o: ["React negatively", "Dwell on it", "Accept but hesitate", "Try again", "Recover quickly"] },
        { q: "23. How do you solve complex problems under adversity?", o: ["Unable to solve", "Struggle often", "Try my best", "Often solve them", "Fully capable"] }
    ];

    const container = document.getElementById('questions-container');
    if (container) {
        questions.forEach((item, index) => {
            const qNum = index + 1;
            let card = document.createElement('div');
            card.className = 'question-card'; 
            
            let questionText = `<p class="question-text">${item.q}</p>`;
            let optionsHtml = '<div class="options">';
            item.o.forEach((option, optionIndex) => {
                const value = optionIndex + 1;
                optionsHtml += `
                    <div class="form-check">
                        <input class="form-check-input" type="radio" name="q${qNum}" id="q${qNum}_${value}" value="${value}" required>
                        <label class="form-check-label" for="q${qNum}_${value}">${option}</label>
                    </div>
                `;
            });
            optionsHtml += '</div>';
            
            card.innerHTML = questionText + optionsHtml;
            container.appendChild(card);
        });

        // Progress bar logic
        const totalQuestions = questions.length;
        const progressBar = document.getElementById('progress-bar');
        const radioButtons = document.querySelectorAll('input[type="radio"]');

        function updateProgress() {
            const checkedRadios = document.querySelectorAll('input[type="radio"]:checked');
            const answeredQuestions = new Set(Array.from(checkedRadios).map(radio => radio.name));
            const progressPercentage = Math.round((answeredQuestions.size / totalQuestions) * 100);
            progressBar.style.width = progressPercentage + '%';
        }

        radioButtons.forEach(radio => {
            radio.addEventListener('change', updateProgress);
        });
    }
});
