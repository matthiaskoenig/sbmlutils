<template>
    <file-upload-form />
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";

/* Components */
import FileUpload from "@/components/FileUploadForm.vue";

@Options({
    components: {
        "file-upload-form": FileUpload,
    },
})
export default class UploadSBML extends Vue {}
</script>

<style lang="scss" scoped></style>
