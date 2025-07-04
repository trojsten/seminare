import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["fileInput", "form", "fileText"]

    onInputChange() {
        for (const file of this.fileInputTarget.files) {
            this.fileTextTarget.textContent = file.name;
        }
        this.formTarget.classList.remove('hidden');
    }

    openFilePicker() {
        this.fileInputTarget.click()
    }
}
