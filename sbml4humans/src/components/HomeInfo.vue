<template>
    <div class="divider">
        <div class="left-container">
            <examples-list></examples-list>
        </div>
        <div class="right-container">
            <upload-sbml></upload-sbml>
        </div>
    </div>
</template>

<script lang="ts">
import { Options, Vue } from "vue-class-component";

/* Components */
import ExamplesListContainer from "@/components/ExamplesListContainer.vue";
import FileUploadForm from "@/components/FileUploadForm.vue";

@Options({
    components: {
        "examples-list": ExamplesListContainer,
        "upload-sbml": FileUploadForm,
    },

    props: {
        msg: String,
    },
})
export default class HomeInfo extends Vue {
    msg!: string;
}
</script>

<style scoped lang="scss">
@import "../assets/styles/scss/components/HomeInfo.scss";
</style>
