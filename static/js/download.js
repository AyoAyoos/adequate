document.addEventListener('DOMContentLoaded', function() {
    
    // Find the download button by its ID
    const downloadButton = document.getElementById('download-btn');

    // Add a click event listener to the button
    downloadButton.addEventListener('click', function() {
        
        // 1. Find the element that contains the content for the PDF
        const element = document.getElementById('pdf-content');

        // 2. Define options for the PDF file
        const options = {
            margin:       1,
            filename:     'classification_results.pdf',
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2 }, // Improves the quality/resolution
            jsPDF:        { unit: 'in', format: 'letter', orientation: 'portrait' }
        };

        // 3. Use html2pdf library to generate the PDF from the element
        //    and automatically trigger the download.
        html2pdf().from(element).set(options).save();
    });
});
