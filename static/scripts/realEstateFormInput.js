const imageInput = document.getElementById('image_input');
const previewGrid = document.getElementById('preview_grid');
let fileList = [];

imageInput.addEventListener('change', (e) => {
    const newFiles = Array.from(e.target.files);
    fileList = fileList.concat(newFiles);
    updateFileInputAndPreviews();
});

function removeFile(index) {
    fileList.splice(index, 1);
    updateFileInputAndPreviews();
}

function updateFileInputAndPreviews() {
    const dt = new DataTransfer();
    fileList.forEach(file => dt.items.add(file));
    imageInput.files = dt.files;

    previewGrid.innerHTML = '';

    fileList.forEach((file, index) => {
        const reader = new FileReader();
        reader.onload = (event) => {
            const card = document.createElement('div');
            card.className = 'border border-line p-2 rounded flex flex-col gap-2 bg-white relative';

            const container = document.createElement('div');
            container.className = 'relative w-full h-32 bg-gray-100 rounded overflow-hidden';

            const img = document.createElement('img');
            img.src = event.target.result;
            img.className = 'w-full h-full object-cover';

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'absolute top-1 right-1 bg-red-600 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold';
            btn.textContent = '×';
            btn.onclick = () => removeFile(index);

            container.appendChild(img);
            container.appendChild(btn);

            const inputAlt = document.createElement('input');
            inputAlt.type = 'text';
            inputAlt.name = 'imagens_alt[]';
            inputAlt.placeholder = 'Descrição da foto...';
            inputAlt.className = 'p-1 text-xs border border-line rounded';
            inputAlt.required = true;

            const inputOrdem = document.createElement('input');
            inputOrdem.type = 'hidden';
            inputOrdem.name = 'imagens_ordem[]';
            inputOrdem.value = index + 1;

            card.appendChild(container);
            card.appendChild(inputAlt);
            card.appendChild(inputOrdem);

            previewGrid.appendChild(card);
        };
        reader.readAsDataURL(file);
    });
}
