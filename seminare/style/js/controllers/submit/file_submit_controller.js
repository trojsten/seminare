import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["fileInput", "form", "errorContainer", "errorMessage"]

    fileSubmits = []

    setFiles() {
        const b = new DataTransfer();
        for (const file of this.fileSubmits) b.items.add(file);
        this.fileInputTarget.files = b.files;
    }

    removeFiles() {
        this.fileSubmits = [];
        this.fileInputTarget.files = new DataTransfer().files;
        console.log(this.formTarget.getElementsByClassName("controller-file-preview"))
        Array.from(this.formTarget.getElementsByClassName("controller-file-preview")).forEach(el => el.remove());
    }

    deleteFileSubmit(event) {
        const to_remove = event.target.parentElement.parentElement
        to_remove.parentElement.removeChild(to_remove)
        const filename = event.params.filename
        for (let i = 0; i < this.fileSubmits.length; i++) {
            if (this.fileSubmits[i].name === filename) {
                this.fileSubmits.splice(i, 1);
                if (this.fileSubmits.length === 0) {
                    this.formTarget.classList.add('hidden');
                }
                this.setFiles();
                return;
            }
        }
    }

    onInputChange() {
        let pdfs = 0, images = 0, other = 0, other_name = null;

        for (const file of [...this.fileSubmits, ...this.fileInputTarget.files]) {
            if (file.type === 'application/pdf') {
                ++pdfs;
            } else if (file.type.startsWith('image/')) {
                ++images;
            } else {
                ++other;
                if (!other_name) {
                    other_name = file.name;
                }
            }
        }

        let error = null;

        if (pdfs > 1 || (images > 0 && pdfs > 0)) {
            error = "Môžeš odovzdať iba jedno PDF alebo viacero obrázkov"
        }
        if (other > 0) {
            error = `Súbor '${other_name}' nie je podporovaný`
        }

        if (error) {
            this.errorContainerTarget.classList.add('flex');
            this.errorContainerTarget.classList.remove('hidden');
            this.errorMessageTarget.innerText = error;
            this.formTarget.classList.add('hidden');
            this.removeFiles()
            return;
        }

        for (const file of this.fileInputTarget.files) {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => {
                this.fileInputTarget.insertAdjacentHTML("beforebegin", `
                    <div class="p-2 text-xs rounded-md bg-gray-100 relative controller-file-preview">
                        <div class="absolute right-3 top-3 bg-white/60 hover:bg-white/80 rounded-full p-1 flex cursor-pointer" data-action="click->submit--file-submit#deleteFileSubmit" data-submit--file-submit-filename-param="${file.name}">
                            <iconify-icon class="size-5" width="none" icon="mdi:close"></iconify-icon>
                        </div>` +
                    (
                        file.type == 'application/pdf'
                            ? `<div class="flex items-center justify-center"><iconify-icon class="size-10" icon="mdi:file-pdf-outline" height="40"></iconify-icon></div>`
                            : `<img src="${reader.result}" class="rounded">`
                    ) +
                    `<div class="mt-1 text-center">
                            ${file.name}
                        </div>
                    </div>`);
            };
        }

        this.fileSubmits.push(...this.fileInputTarget.files);

        this.errorContainerTarget.classList.add('hidden');
        this.errorContainerTarget.classList.remove('flex');

        this.setFiles();
        this.formTarget.classList.remove('hidden');
    }

    openFilePicker() {
        this.fileInputTarget.click()
    }
}
