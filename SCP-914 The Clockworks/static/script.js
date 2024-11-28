document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('uploadForm');
    const outputContainer = document.getElementById('output-container');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        outputContainer.textContent = "Processing...";

        const formData = new FormData(form);
        const response = await fetch('/process', {
            method: 'POST',
            body: formData,
        });

        const result = await response.json();
        if (result.success) {
            outputContainer.innerHTML = `<p>Output File: <a href="${result.output_url}" download>Download Here</a></p>`;
        } else {
            outputContainer.textContent = "Error: " + result.error;
        }
    });
});
