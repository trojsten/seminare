import { Controller } from "@hotwired/stimulus";

export default class extends Controller {
    static targets = ["fileInput", "dropZone", "form", "fileText"]

    onInputChange() {
        for (const file of this.fileInputTarget.files) {
            this.fileTextTarget.textContent = file.name;
        }
        this.formTarget.classList.remove('hidden');
    }

    onDrop(e) {
        e.preventDefault();
        this.fileInputTarget.files = e.dataTransfer.files;
        this.onInputChange();
        this.dropZoneTarget.classList.add('bg-gray-100');
        this.dropZoneTarget.classList.remove('border-green-500');
        this.dropZoneTarget.classList.remove('bg-green-100');
    }

    onDragOver(e) {
        const fileItems = [...e.dataTransfer.items].filter(
            (item) => item.kind === "file",
        );
        if (fileItems.length > 0) {
            e.preventDefault();
            e.dataTransfer.dropEffect = "copy";
            this.dropZoneTarget.classList.remove('bg-gray-100');
            this.dropZoneTarget.classList.add('bg-green-100');
            this.dropZoneTarget.classList.add('border-green-500');
        }
    }

    onDragLeave(e) {
        const fileItems = [...e.dataTransfer.items].filter(
            (item) => item.kind === "file",
        );
        if (fileItems.length > 0) {
            e.preventDefault();
            this.dropZoneTarget.classList.add('bg-gray-100');
            this.dropZoneTarget.classList.remove('border-green-500');
            this.dropZoneTarget.classList.remove('bg-green-100');
        }
    }
}
