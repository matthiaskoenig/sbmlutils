<template>
    <!-- {{ addInfo }} -->
    <div class="p-d-flex p-mt-2">
        <Tag :value="qualifier" severity="success" class="qualifier" />
        <Tag
            v-if="addInfo.collection"
            :value="addInfo.collection"
            severity="info"
            class="collection"
        />
        <Tag
            v-if="addInfo.term"
            :value="addInfo.term"
            severity="warning"
            class="resource"
        >
            <a
                v-if="addInfo.term"
                :href="addInfo.resource"
                target="_blank"
                class="resource"
                >{{ addInfo.term }}</a
            >
            <a v-else :href="addInfo.resource" target="_blank" class="resource">{{
                addInfo.resource
            }}</a>
        </Tag>
    </div>
    <div v-if="addInfo.errors && addInfo.errors.length">
        <code
            v-for="error in addInfo.errors"
            :key="error"
            class="text-error"
            style="font-size: smaller"
            >Error: {{ error }}</code
        >
    </div>
    <div v-if="addInfo.warnings && addInfo.warnings.length">
        <code
            v-for="warning in addInfo.warnings"
            :key="warning"
            class="text-warning"
            style="font-size: smaller"
            >{{ warning }}</code
        >
    </div>

    <div class="p-mt-1 p-mb-3 p-ml-2" v-if="addInfo != null">
        <strong v-if="addInfo.label">{{ addInfo.label }}</strong>
        <span v-if="addInfo.description != null"
            ><br />
            {{ addInfo.description }}</span
        >

        <div v-if="addInfo.synonyms != null && addInfo.synonyms.length > 0">
            <strong>Synonyms</strong>
            <div class="p-ml-3">
                <li v-for="synonym in addInfo.synonyms" :key="synonym">
                    {{ synonym.name }}
                </li>
            </div>
        </div>
        <div v-if="addInfo.xrefs && addInfo.xrefs.length > 0">
            <strong>Cross references</strong>
            <div class="p-ml-3">
                <span v-for="xref in addInfo.xrefs" :key="xref">
                    <li v-if="xref.url">
                        <a :href="xref.url" target="_blank"
                            >{{ xref.database }}:{{ xref.id }}</a
                        >
                    </li>
                    <li v-else>{{ xref.database }}:{{ xref.id }}</li>
                </span>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { fetchAdditionalInfo } from "@/helpers/additionalInfoUtils";

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
        fetchAdditionalInfo(this.resource).then((res) => {
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
.collection {
    border-radius: 0 0 0 0;
    padding: 0 5px !important;
}

.resource {
    color: black;
    border-radius: 0px 5px 5px 0;
    height: inherit !important;
}

.p-tag {
    padding: 0 5px !important;
}
</style>
