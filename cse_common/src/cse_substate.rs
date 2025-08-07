pub trait CSESubstateTrait<T>
{
  fn set_state(&mut self, state: T);
  fn consume_trigger(&mut self) -> bool;
  fn get_state(&self) -> T;
}

#[derive(Clone)]
pub struct CSESubstate<T: Copy + Clone>
{
  state: T,
  triggered: bool,
}

impl<T: Copy + Clone> CSESubstate<T>
{
  pub fn new(initial_state: T) -> Self
  {
    return CSESubstate { state: initial_state, triggered: false }
  }
}

impl<T: Copy + Clone> CSESubstateTrait<T> for CSESubstate<T>
{
  fn set_state(&mut self, state: T) 
  {
    self.state = state;
    self.triggered = true;
  }

  fn consume_trigger(&mut self) -> bool
  {
    if self.triggered
    {
      self.triggered = false;
      return true;
    }

    return false;
  }

  fn get_state(&self) -> T
  {
    return self.state;
  }
}