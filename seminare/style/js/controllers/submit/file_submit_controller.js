import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["fileInput", "form"]

    fileSubmits = []

    setFiles() {
        const b = new DataTransfer();
        for (const file of this.fileSubmits) b.items.add(file);
        this.fileInputTarget.files = b.files;
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
        for (const file of this.fileInputTarget.files) {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => {
                this.fileInputTarget.insertAdjacentHTML("beforebegin", `
                    <div class="p-2 text-xs rounded-md bg-gray-100 relative">
                        <div class="absolute right-3 top-3 bg-white/60 hover:bg-white/80 rounded-full p-1 flex cursor-pointer" data-action="click->submit--file-submit#deleteFileSubmit" data-submit--file-submit-filename-param="${file.name}">
                            <iconify-icon class="size-5" width="none" icon="mdi:close"></iconify-icon>
                        </div>
                        <img src="${reader.result}" class="rounded">
                        <div class="mt-1 text-center">
                            ${file.name}
                        </div>
                    </div>`);
            };
        }
        this.fileSubmits.push(...this.fileInputTarget.files);
        this.setFiles();
        this.formTarget.classList.remove('hidden');
    }

    openFilePicker() {
        this.fileInputTarget.click()
    }
}
