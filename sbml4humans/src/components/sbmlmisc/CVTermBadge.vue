<template>
    <div class="p-d-flex p-mt-2">
        <Tag :value="qualifier" severity="success" class="qualifier"></Tag>
        <Tag :value="qualifier" severity="warning" class="resource">
            <a :href="resource" target="_blank" class="resource">{{ resource }}</a>
        </Tag>
    </div>
    <div class="p-mt-1 p-mb-2 p-ml-2" v-if="addInfo != null">
        <strong>{{ addInfo.name }}:</strong> {{ addInfo.definition }} <br />
        <span v-if="addInfo.synonyms != null"
            >Synonyms: {{ addInfo.synonyms.join() }}</span
        >
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import additionalInfoUtils from "@/helpers/additionalInfoUtils";

export default defineComponent({
    props: {
        qualifier: {
            type: String,
            default: "",
        },
        resource: {
            type: String,
            default: "",
        },
    },

    data() {
        return {
            addInfo: {},
        };
    },

    created() {
        const parts = this.resource.split("/");
        const resourceID = parts[parts.length - 1];
        additionalInfoUtils.fetchAdditionalInfo(resourceID).then((res) => {
            this.addInfo = res as Record<string, unknown>;
        });
    },
});
</script>

<style lang="scss" scoped>
.qualifier {
    border-radius: 5px 0 0 5px;
    padding: 0 5px !important;
}

.resource {
    color: black;
    border-radius: 0px 5px 5px 0;
}

.p-tag {
    padding: 0 5px !important;
}
</style>
