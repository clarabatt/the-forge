<template>
  <div class="resume-paper">
    <div class="resume-placeholder">
      <div class="resume-line resume-line--name" />
      <div class="resume-line resume-line--contact" />
      <div class="resume-spacer" />
      <div class="resume-line resume-line--section" />
      <div class="resume-line" />
      <div class="resume-line resume-line--short" />
      <div class="resume-line" />
      <div class="resume-line resume-line--medium" />
      <div class="resume-spacer" />
      <div class="resume-line resume-line--section" />
      <div class="resume-line" />
      <div class="resume-line resume-line--short" />
      <div class="resume-line" />
      <div class="resume-line resume-line--medium" />
      <div class="resume-line resume-line--short" />
      <div class="resume-spacer" />
      <div class="resume-line resume-line--section" />
      <div class="resume-line resume-line--medium" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
.resume-paper {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  padding: 48px 56px;
  min-height: 640px;
}

.resume-placeholder {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.resume-line {
  height: 10px;
  background: var(--color-border);
  border-radius: 4px;
  width: 100%;

  &--name {
    height: 20px;
    width: 44%;
    background: #d1d5db;
  }

  &--contact {
    width: 32%;
    background: #d1d5db;
    opacity: 0.7;
  }

  &--section {
    height: 13px;
    width: 28%;
    background: #d1d5db;
    opacity: 0.6;
  }

  &--short {
    width: 42%;
  }

  &--medium {
    width: 68%;
  }
}

.resume-spacer {
  height: 14px;
}
</style>
