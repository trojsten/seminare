import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["filePicker", "fileForm"]

    fileSubmits = []

    setFiles() {
        const b = new DataTransfer();
        for (const file of this.fileSubmits) b.items.add(file);
        this.filePickerTarget.files = b.files;
    }

    deleteFileSubmit(event) {
        const to_remove = event.target.parentElement.parentElement
        to_remove.parentElement.removeChild(to_remove)
        const filename = event.params.filename
        for (let i = 0; i < this.fileSubmits.length; i++) {
            if (this.fileSubmits[i].name === filename) {
                this.fileSubmits.splice(i, 1);
                if (this.fileSubmits.length === 0) {
                    this.fileFormTarget.classList.add('hidden');
                }
                this.setFiles();
                return;
            }
        }
    }

    onFileSubmit() {
        for (const file of this.filePickerTarget.files) {
            const reader = new FileReader();
            reader.readAsDataURL(file);
            reader.onload = () => {
                this.filePickerTarget.insertAdjacentHTML("beforebegin", `
                    <div class="p-2 text-xs rounded-md bg-gray-100 relative">
                        <div class="absolute right-3 top-3 bg-white/60 hover:bg-white/80 rounded-full p-1 flex cursor-pointer" data-action="click->submit--submit#deleteFileSubmit" data-submit--submit-filename-param="${file.name}">
                            <iconify-icon class="size-5" width="none" icon="mdi:close"></iconify-icon>
                        </div>
                        <img src="${reader.result}" class="rounded">
                        <div class="mt-1 text-center">
                            ${file.name}
                        </div>
                    </div>`);
            };
        }
        this.fileSubmits.push(...this.filePickerTarget.files);
        this.setFiles();
        this.fileFormTarget.classList.remove('hidden');
    }

    openFilePicker() {
        this.filePickerTarget.click()
    }
}
